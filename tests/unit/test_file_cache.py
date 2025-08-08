"""
Unit tests for FileCache system

Tests the file caching system including:
- Cache hit/miss behavior
- File modification detection
- Cache eviction policies
- Memory management
- Performance statistics
- Thread safety
"""

import pytest
import tempfile
import json
import yaml
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

from equitrcoder.core.file_cache import (
    FileCache,
    CacheEntry,
    CacheStats,
    get_file_cache,
    configure_file_cache,
    cached_file_read,
    invalidate_file_cache,
    get_cache_stats,
    clear_file_cache
)


class TestCacheEntry:
    """Test suite for CacheEntry"""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation and basic properties"""
        entry = CacheEntry(
            content="test content",
            file_path="/test/path.txt",
            file_size=100,
            modification_time=1234567890.0,
            content_hash="abc123"
        )
        
        assert entry.content == "test content"
        assert entry.file_path == "/test/path.txt"
        assert entry.file_size == 100
        assert entry.modification_time == 1234567890.0
        assert entry.content_hash == "abc123"
        assert entry.access_count == 0
    
    def test_cache_entry_validity(self):
        """Test cache entry validity checking"""
        entry = CacheEntry(
            content="test",
            file_path="/test.txt",
            file_size=10,
            modification_time=time.time()
        )
        
        # Should be valid immediately
        assert entry.is_valid(max_age_seconds=300)
        
        # Should be invalid after TTL
        assert not entry.is_valid(max_age_seconds=0)
    
    def test_update_access(self):
        """Test access count and time updating"""
        entry = CacheEntry(
            content="test",
            file_path="/test.txt",
            file_size=10,
            modification_time=time.time()
        )
        
        initial_access_count = entry.access_count
        initial_access_time = entry.last_access
        
        time.sleep(0.01)  # Small delay to ensure time difference
        entry.update_access()
        
        assert entry.access_count == initial_access_count + 1
        assert entry.last_access > initial_access_time


class TestCacheStats:
    """Test suite for CacheStats"""
    
    def test_cache_stats_creation(self):
        """Test CacheStats creation and default values"""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_requests == 0
        assert stats.cache_size == 0
        assert stats.memory_usage_bytes == 0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats(hits=7, misses=3, total_requests=10)
        
        assert stats.hit_rate == 70.0
        assert stats.miss_rate == 30.0
    
    def test_hit_rate_with_zero_requests(self):
        """Test hit rate calculation with zero requests"""
        stats = CacheStats()
        
        assert stats.hit_rate == 0.0
        assert stats.miss_rate == 100.0


class TestFileCache:
    """Test suite for FileCache"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.cache = FileCache(max_size=5, max_memory_mb=1, default_ttl_seconds=60)
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_file(self, filename: str, content: str) -> Path:
        """Create a temporary file with given content"""
        file_path = self.temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def create_temp_json(self, filename: str, data: dict) -> Path:
        """Create a temporary JSON file"""
        file_path = self.temp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return file_path
    
    def create_temp_yaml(self, filename: str, data: dict) -> Path:
        """Create a temporary YAML file"""
        file_path = self.temp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        return file_path
    
    def test_cache_initialization(self):
        """Test FileCache initialization"""
        cache = FileCache(max_size=10, max_memory_mb=5, default_ttl_seconds=120)
        
        assert cache.max_size == 10
        assert cache.max_memory_bytes == 5 * 1024 * 1024
        assert cache.default_ttl == 120
        assert len(cache._cache) == 0
    
    def test_text_file_caching(self):
        """Test caching of text files"""
        file_path = self.create_temp_file("test.txt", "Hello, World!")
        
        # First read should be a cache miss
        content1 = self.cache.get_file_content(file_path)
        assert content1 == "Hello, World!"
        
        stats = self.cache.get_stats()
        assert stats.misses == 1
        assert stats.hits == 0
        assert stats.cache_size == 1
        
        # Second read should be a cache hit
        content2 = self.cache.get_file_content(file_path)
        assert content2 == "Hello, World!"
        
        stats = self.cache.get_stats()
        assert stats.misses == 1
        assert stats.hits == 1
        assert stats.cache_size == 1
    
    def test_json_file_caching(self):
        """Test caching of JSON files"""
        test_data = {"name": "test", "value": 42, "items": [1, 2, 3]}
        file_path = self.create_temp_json("test.json", test_data)
        
        content = self.cache.get_file_content(file_path)
        assert content == test_data
        
        # Verify it's cached
        stats = self.cache.get_stats()
        assert stats.cache_size == 1
    
    def test_yaml_file_caching(self):
        """Test caching of YAML files"""
        test_data = {"config": {"debug": True, "port": 8080}}
        file_path = self.create_temp_yaml("test.yaml", test_data)
        
        content = self.cache.get_file_content(file_path)
        assert content == test_data
        
        # Verify it's cached
        stats = self.cache.get_stats()
        assert stats.cache_size == 1
    
    def test_file_modification_detection(self):
        """Test that cache detects file modifications"""
        file_path = self.create_temp_file("test.txt", "Original content")
        
        # First read
        content1 = self.cache.get_file_content(file_path)
        assert content1 == "Original content"
        
        # Modify file
        time.sleep(0.01)  # Ensure different modification time
        file_path.write_text("Modified content", encoding='utf-8')
        
        # Second read should detect modification and reload
        content2 = self.cache.get_file_content(file_path)
        assert content2 == "Modified content"
        
        # Should have 2 misses (original + after modification)
        stats = self.cache.get_stats()
        assert stats.misses == 2
    
    def test_cache_invalidation(self):
        """Test manual cache invalidation"""
        file_path = self.create_temp_file("test.txt", "Test content")
        
        # Cache the file
        self.cache.get_file_content(file_path)
        assert self.cache.get_stats().cache_size == 1
        
        # Invalidate
        result = self.cache.invalidate_file(file_path)
        assert result is True
        assert self.cache.get_stats().cache_size == 0
        
        # Invalidating non-existent file should return False
        result = self.cache.invalidate_file(file_path)
        assert result is False
    
    def test_cache_pattern_invalidation(self):
        """Test pattern-based cache invalidation"""
        # Create multiple files
        file1 = self.create_temp_file("test1.txt", "Content 1")
        file2 = self.create_temp_file("test2.txt", "Content 2")
        file3 = self.create_temp_file("config.yaml", "key: value")
        
        # Cache all files
        self.cache.get_file_content(file1)
        self.cache.get_file_content(file2)
        self.cache.get_file_content(file3)
        
        assert self.cache.get_stats().cache_size == 3
        
        # Invalidate all .txt files
        invalidated = self.cache.invalidate_pattern("*.txt")
        assert invalidated == 2
        assert self.cache.get_stats().cache_size == 1
    
    def test_cache_size_limit(self):
        """Test cache size limit enforcement"""
        # Create more files than cache limit
        files = []
        for i in range(7):  # Cache limit is 5
            file_path = self.create_temp_file(f"test{i}.txt", f"Content {i}")
            files.append(file_path)
        
        # Cache all files
        for file_path in files:
            self.cache.get_file_content(file_path)
        
        # Should not exceed max size
        stats = self.cache.get_stats()
        assert stats.cache_size <= self.cache.max_size
        assert stats.evictions > 0
    
    def test_ttl_expiration(self):
        """Test TTL-based cache expiration"""
        file_path = self.create_temp_file("test.txt", "Test content")
        
        # Cache with very short TTL
        content1 = self.cache.get_file_content(file_path, ttl_seconds=0.01)
        assert content1 == "Test content"
        
        # Wait for TTL to expire
        time.sleep(0.02)
        
        # Should reload from disk
        content2 = self.cache.get_file_content(file_path, ttl_seconds=0.01)
        assert content2 == "Test content"
        
        # Should have 2 misses due to TTL expiration
        stats = self.cache.get_stats()
        assert stats.misses == 2
    
    def test_nonexistent_file(self):
        """Test handling of non-existent files"""
        with pytest.raises(FileNotFoundError):
            self.cache.get_file_content("/nonexistent/file.txt")
    
    def test_custom_parser(self):
        """Test using custom parser"""
        file_path = self.create_temp_file("test.json", '{"key": "value"}')
        
        # Parse as text instead of JSON
        content = self.cache.get_file_content(file_path, parser="text")
        assert content == '{"key": "value"}'
        assert isinstance(content, str)
    
    def test_cache_clear(self):
        """Test clearing the entire cache"""
        # Cache some files
        file1 = self.create_temp_file("test1.txt", "Content 1")
        file2 = self.create_temp_file("test2.txt", "Content 2")
        
        self.cache.get_file_content(file1)
        self.cache.get_file_content(file2)
        
        assert self.cache.get_stats().cache_size == 2
        
        # Clear cache
        self.cache.clear_cache()
        assert self.cache.get_stats().cache_size == 0
    
    def test_cached_files_info(self):
        """Test getting information about cached files"""
        file_path = self.create_temp_file("test.txt", "Test content")
        
        self.cache.get_file_content(file_path)
        
        cached_files = self.cache.get_cached_files()
        assert len(cached_files) == 1
        
        file_info = list(cached_files.values())[0]
        assert 'file_size' in file_info
        assert 'cache_time' in file_info
        assert 'access_count' in file_info
        assert 'content_hash' in file_info
    
    def test_thread_safety(self):
        """Test thread safety of cache operations"""
        file_path = self.create_temp_file("test.txt", "Thread test content")
        
        results = []
        errors = []
        
        def cache_worker():
            try:
                for _ in range(10):
                    content = self.cache.get_file_content(file_path)
                    results.append(content)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0
        assert len(results) == 50
        assert all(result == "Thread test content" for result in results)


class TestGlobalCacheFunctions:
    """Test suite for global cache functions"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear global cache before each test
        clear_file_cache()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_file_cache()
    
    def create_temp_file(self, filename: str, content: str) -> Path:
        """Create a temporary file with given content"""
        file_path = self.temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def test_get_file_cache(self):
        """Test getting global file cache instance"""
        cache1 = get_file_cache()
        cache2 = get_file_cache()
        
        # Should return the same instance (singleton)
        assert cache1 is cache2
    
    def test_configure_file_cache(self):
        """Test configuring global file cache"""
        cache = configure_file_cache(max_size=20, max_memory_mb=10, default_ttl_seconds=600)
        
        assert cache.max_size == 20
        assert cache.max_memory_bytes == 10 * 1024 * 1024
        assert cache.default_ttl == 600
    
    def test_cached_file_read(self):
        """Test convenience function for cached file reading"""
        file_path = self.create_temp_file("test.txt", "Convenience test")
        
        content = cached_file_read(file_path)
        assert content == "Convenience test"
        
        # Should be cached
        stats = get_cache_stats()
        assert stats.cache_size == 1
    
    def test_invalidate_file_cache(self):
        """Test convenience function for cache invalidation"""
        file_path = self.create_temp_file("test.txt", "Test content")
        
        # Cache the file
        cached_file_read(file_path)
        assert get_cache_stats().cache_size == 1
        
        # Invalidate
        result = invalidate_file_cache(file_path)
        assert result is True
        assert get_cache_stats().cache_size == 0
    
    def test_get_cache_stats(self):
        """Test convenience function for getting cache statistics"""
        file_path = self.create_temp_file("test.txt", "Stats test")
        
        # Get initial stats
        initial_stats = get_cache_stats()
        initial_requests = initial_stats.total_requests
        
        # Cache a file
        cached_file_read(file_path)
        
        # Updated stats
        stats = get_cache_stats()
        assert stats.total_requests == initial_requests + 1
        assert stats.cache_size >= 1
    
    def test_clear_file_cache(self):
        """Test convenience function for clearing cache"""
        file_path = self.create_temp_file("test.txt", "Clear test")
        
        # Cache a file
        cached_file_read(file_path)
        assert get_cache_stats().cache_size == 1
        
        # Clear cache
        clear_file_cache()
        assert get_cache_stats().cache_size == 0


if __name__ == '__main__':
    pytest.main([__file__])