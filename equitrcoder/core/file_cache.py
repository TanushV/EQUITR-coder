"""
File Caching System for EQUITR Coder

This module provides intelligent caching for file operations to eliminate
repeated file reading/parsing operations and improve performance.

Features:
- Intelligent caching for configuration files
- Cache invalidation and refresh mechanisms
- Memory-efficient caching with size limits
- File modification time tracking
- Cache hit rate monitoring
"""

import os
# import time  # Unused
import hashlib
import threading
from typing import Any, Dict, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging
# import weakref  # Unused
import json
import yaml

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached file entry with metadata"""
    content: Any
    file_path: str
    file_size: int
    modification_time: float
    cache_time: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    content_hash: str = ""
    
    def is_valid(self, max_age_seconds: int = 300) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - self.cache_time).total_seconds()
        return age < max_age_seconds
    
    def update_access(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_access = datetime.now()


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    cache_size: int = 0
    memory_usage_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate as percentage"""
        return 100.0 - self.hit_rate


from .interfaces import ICache  # noqa: E402

class FileCache(ICache[Any]):
    """
    Intelligent file caching system with automatic invalidation and performance monitoring
    """
    
    def __init__(self, 
                 max_size: int = 100,
                 max_memory_mb: int = 50,
                 default_ttl_seconds: int = 300,
                 enable_stats: bool = True):
        """
        Initialize the file cache
        
        Args:
            max_size: Maximum number of files to cache
            max_memory_mb: Maximum memory usage in MB
            default_ttl_seconds: Default time-to-live for cache entries
            enable_stats: Whether to collect performance statistics
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl_seconds
        self.enable_stats = enable_stats
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        # File parsers for different file types
        self._parsers: Dict[str, Callable] = {
            '.json': self._parse_json,
            '.yaml': self._parse_yaml,
            '.yml': self._parse_yaml,
            '.txt': self._parse_text,
            '.py': self._parse_text,
            '.md': self._parse_text,
        }
        
        logger.info(f"FileCache initialized: max_size={max_size}, max_memory={max_memory_mb}MB, ttl={default_ttl_seconds}s")
    
    def get_file_content(self, 
                        file_path: Union[str, Path], 
                        parser: Optional[str] = None,
                        ttl_seconds: Optional[int] = None) -> Any:
        """
        Get file content from cache or load from disk
        
        Args:
            file_path: Path to the file
            parser: Specific parser to use ('json', 'yaml', 'text')
            ttl_seconds: Custom TTL for this file
            
        Returns:
            File content (parsed if applicable)
        """
        file_path = str(Path(file_path).resolve())
        ttl = ttl_seconds or self.default_ttl
        
        with self._lock:
            self._stats.total_requests += 1
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check cache first
            cache_entry = self._cache.get(file_path)
            if cache_entry and self._is_cache_valid(cache_entry, file_path, ttl):
                cache_entry.update_access()
                self._stats.hits += 1
                logger.debug(f"Cache hit for {file_path}")
                return cache_entry.content
            
            # Cache miss - load from disk
            self._stats.misses += 1
            logger.debug(f"Cache miss for {file_path}")
            
            content = self._load_and_parse_file(file_path, parser)
            self._store_in_cache(file_path, content)
            
            return content
    
    def invalidate_file(self, file_path: Union[str, Path]) -> bool:
        """
        Invalidate a specific file in the cache
        
        Args:
            file_path: Path to the file to invalidate
            
        Returns:
            True if file was in cache and removed
        """
        file_path = str(Path(file_path).resolve())
        
        with self._lock:
            if file_path in self._cache:
                del self._cache[file_path]
                self._update_cache_stats()
                logger.debug(f"Invalidated cache for {file_path}")
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cached files matching a pattern
        
        Args:
            pattern: File path pattern (supports wildcards)
            
        Returns:
            Number of files invalidated
        """
        import fnmatch
        
        with self._lock:
            files_to_remove = []
            for file_path in self._cache.keys():
                if fnmatch.fnmatch(file_path, pattern):
                    files_to_remove.append(file_path)
            
            for file_path in files_to_remove:
                del self._cache[file_path]
            
            self._update_cache_stats()
            logger.info(f"Invalidated {len(files_to_remove)} files matching pattern: {pattern}")
            return len(files_to_remove)
    
    def clear_cache(self) -> None:
        """Clear all cached files"""
        with self._lock:
            self._cache.clear()
            self._update_cache_stats()
            logger.info("Cache cleared")
    
    # ICache interface implementation
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache (ICache interface)"""
        try:
            return self.get_file_content(key)
        except (FileNotFoundError, Exception):
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in cache (ICache interface) - Not applicable for file cache"""
        logger.warning("FileCache.set() not supported - files are cached automatically when read")
        return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache (ICache interface)"""
        return self.invalidate_file(key)
    
    async def clear(self) -> bool:
        """Clear all items from cache (ICache interface)"""
        try:
            self.clear_cache()
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache (ICache interface)"""
        with self._lock:
            return key in self._cache
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics"""
        with self._lock:
            self._update_cache_stats()
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                total_requests=self._stats.total_requests,
                cache_size=len(self._cache),
                memory_usage_bytes=self._stats.memory_usage_bytes
            )
    
    def get_cached_files(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all cached files"""
        with self._lock:
            result = {}
            for file_path, entry in self._cache.items():
                result[file_path] = {
                    'file_size': entry.file_size,
                    'cache_time': entry.cache_time.isoformat(),
                    'access_count': entry.access_count,
                    'last_access': entry.last_access.isoformat(),
                    'content_hash': entry.content_hash
                }
            return result
    
    def _is_cache_valid(self, entry: CacheEntry, file_path: str, ttl: int) -> bool:
        """Check if a cache entry is still valid"""
        # Check TTL
        if not entry.is_valid(ttl):
            return False
        
        # Check if file has been modified
        try:
            current_mtime = os.path.getmtime(file_path)
            current_size = os.path.getsize(file_path)
            
            if (current_mtime != entry.modification_time or 
                current_size != entry.file_size):
                return False
        except OSError:
            # File no longer exists or is inaccessible
            return False
        
        return True
    
    def _load_and_parse_file(self, file_path: str, parser: Optional[str] = None) -> Any:
        """Load and parse a file from disk"""
        try:
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            # modification_time = stat.st_mtime
            
            # Determine parser
            if parser:
                parse_func = self._get_parser_by_name(parser)
            else:
                file_ext = Path(file_path).suffix.lower()
                parse_func = self._parsers.get(file_ext, self._parse_text)
            
            # Load and parse content
            content = parse_func(file_path)
            
            logger.debug(f"Loaded file {file_path} ({file_size} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")
            raise
    
    def _store_in_cache(self, file_path: str, content: Any) -> None:
        """Store content in cache with automatic eviction if needed"""
        try:
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            modification_time = stat.st_mtime
            
            # Calculate content hash for integrity checking
            content_str = str(content) if not isinstance(content, (str, bytes)) else content
            content_hash = hashlib.md5(str(content_str).encode()).hexdigest()
            
            # Create cache entry
            entry = CacheEntry(
                content=content,
                file_path=file_path,
                file_size=file_size,
                modification_time=modification_time,
                content_hash=content_hash
            )
            
            # Check if we need to evict entries
            self._ensure_cache_limits()
            
            # Store in cache
            self._cache[file_path] = entry
            self._update_cache_stats()
            
            logger.debug(f"Cached file {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to cache file {file_path}: {e}")
    
    def _ensure_cache_limits(self) -> None:
        """Ensure cache doesn't exceed size and memory limits"""
        # Check size limit
        while len(self._cache) >= self.max_size:
            self._evict_lru_entry()
        
        # Check memory limit
        current_memory = self._calculate_memory_usage()
        while current_memory > self.max_memory_bytes and self._cache:
            self._evict_lru_entry()
            current_memory = self._calculate_memory_usage()
    
    def _evict_lru_entry(self) -> None:
        """Evict the least recently used cache entry"""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_path = min(self._cache.keys(), 
                      key=lambda k: self._cache[k].last_access)
        
        del self._cache[lru_path]
        self._stats.evictions += 1
        logger.debug(f"Evicted LRU entry: {lru_path}")
    
    def _calculate_memory_usage(self) -> int:
        """Calculate approximate memory usage of cached content"""
        total_size = 0
        for entry in self._cache.values():
            # Rough estimation of memory usage
            content_size = len(str(entry.content).encode('utf-8'))
            total_size += content_size + 1024  # Add overhead for metadata
        return total_size
    
    def _update_cache_stats(self) -> None:
        """Update cache statistics"""
        self._stats.cache_size = len(self._cache)
        self._stats.memory_usage_bytes = self._calculate_memory_usage()
    
    def _get_parser_by_name(self, parser_name: str) -> Callable:
        """Get parser function by name"""
        parser_map = {
            'json': self._parse_json,
            'yaml': self._parse_yaml,
            'yml': self._parse_yaml,
            'text': self._parse_text,
        }
        
        if parser_name not in parser_map:
            raise ValueError(f"Unknown parser: {parser_name}")
        
        return parser_map[parser_name]
    
    def _parse_json(self, file_path: str) -> Any:
        """Parse JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _parse_yaml(self, file_path: str) -> Any:
        """Parse YAML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _parse_text(self, file_path: str) -> str:
        """Parse text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


# Global cache instance
_global_cache: Optional[FileCache] = None
_cache_lock = threading.Lock()


def get_file_cache() -> FileCache:
    """Get the global file cache instance"""
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = FileCache()
    
    return _global_cache


def configure_file_cache(max_size: int = 100,
                        max_memory_mb: int = 50,
                        default_ttl_seconds: int = 300) -> FileCache:
    """Configure the global file cache with custom settings"""
    global _global_cache
    
    with _cache_lock:
        _global_cache = FileCache(
            max_size=max_size,
            max_memory_mb=max_memory_mb,
            default_ttl_seconds=default_ttl_seconds
        )
    
    return _global_cache


def cached_file_read(file_path: Union[str, Path], 
                    parser: Optional[str] = None,
                    ttl_seconds: Optional[int] = None) -> Any:
    """Convenience function for cached file reading"""
    cache = get_file_cache()
    return cache.get_file_content(file_path, parser, ttl_seconds)


def invalidate_file_cache(file_path: Union[str, Path]) -> bool:
    """Convenience function for cache invalidation"""
    cache = get_file_cache()
    return cache.invalidate_file(file_path)


def get_cache_stats() -> CacheStats:
    """Convenience function for getting cache statistics"""
    cache = get_file_cache()
    return cache.get_stats()


def clear_file_cache() -> None:
    """Convenience function for clearing the cache"""
    cache = get_file_cache()
    cache.clear_cache()