"""
Unit tests for String Optimizer

Tests the string optimization system including:
- OptimizedStringBuilder functionality
- ContextBuilder operations
- StringTemplateEngine rendering
- Performance monitoring
- Memory efficiency
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from equitrcoder.core.string_optimizer import (
    ContextBuilder,
    OptimizedStringBuilder,
    StringOperationMonitor,
    StringOperationStats,
    StringTemplateEngine,
    build_context_efficiently,
    efficient_concatenate,
    efficient_format,
    get_string_monitor,
    get_template_engine,
    optimized_join,
)


class TestStringOperationStats:
    """Test suite for StringOperationStats"""

    def test_stats_creation(self):
        """Test StringOperationStats creation and default values"""
        stats = StringOperationStats()

        assert stats.total_operations == 0
        assert stats.total_time_seconds == 0.0
        assert stats.total_memory_bytes == 0
        assert stats.concatenations == 0
        assert stats.context_builds == 0
        assert stats.template_renders == 0

    def test_average_calculations(self):
        """Test average time and memory calculations"""
        stats = StringOperationStats(
            total_operations=10, total_time_seconds=2.0, total_memory_bytes=10240
        )

        assert stats.average_time_ms == 200.0  # 2.0s / 10 ops * 1000ms/s
        assert stats.average_memory_kb == 1.0  # 10240 bytes / 10 ops / 1024 bytes/KB

    def test_zero_operations(self):
        """Test calculations with zero operations"""
        stats = StringOperationStats()

        assert stats.average_time_ms == 0.0
        assert stats.average_memory_kb == 0.0


class TestOptimizedStringBuilder:
    """Test suite for OptimizedStringBuilder"""

    def test_basic_append(self):
        """Test basic string appending"""
        builder = OptimizedStringBuilder()

        result = builder.append("Hello").append(" ").append("World").to_string()
        assert result == "Hello World"
        assert len(builder) == 11

    def test_append_line(self):
        """Test appending lines with newlines"""
        builder = OptimizedStringBuilder()

        result = (
            builder.append_line("Line 1")
            .append_line("Line 2")
            .append_line()
            .to_string()
        )

        assert result == "Line 1\nLine 2\n\n"

    def test_append_lines(self):
        """Test appending multiple lines at once"""
        builder = OptimizedStringBuilder()
        lines = ["First", "Second", "Third"]

        result = builder.append_lines(lines).to_string()
        assert result == "First\nSecond\nThird\n"

    def test_append_separator(self):
        """Test appending separator lines"""
        builder = OptimizedStringBuilder()

        result = builder.append_separator("-", 5).to_string()
        assert result == "-----\n"

    def test_append_formatted(self):
        """Test formatted string appending"""
        builder = OptimizedStringBuilder()

        result = builder.append_formatted(
            "Hello {name}, you are {age} years old", name="Alice", age=30
        ).to_string()
        assert result == "Hello Alice, you are 30 years old"

    def test_append_indented(self):
        """Test indented text appending"""
        builder = OptimizedStringBuilder()

        result = builder.append_indented("Line 1\nLine 2", indent=2).to_string()
        assert result == "  Line 1\n  Line 2"

    def test_clear(self):
        """Test clearing the builder"""
        builder = OptimizedStringBuilder()

        builder.append("Some text")
        assert len(builder) > 0

        builder.clear()
        assert len(builder) == 0
        assert builder.to_string() == ""

    def test_context_manager(self):
        """Test using builder as context manager"""
        with OptimizedStringBuilder() as builder:
            builder.append("Test content")
            result = builder.to_string()

        assert result == "Test content"

    def test_none_handling(self):
        """Test handling of None values"""
        builder = OptimizedStringBuilder()

        result = builder.append(None).append("text").append(None).to_string()
        assert result == "text"

    def test_non_string_types(self):
        """Test handling of non-string types"""
        builder = OptimizedStringBuilder()

        result = (
            builder.append(42)
            .append(" ")
            .append(3.14)
            .append(" ")
            .append(True)
            .to_string()
        )

        assert result == "42 3.14 True"


class TestContextBuilder:
    """Test suite for ContextBuilder"""

    def test_basic_context_building(self):
        """Test basic context building"""
        builder = ContextBuilder(max_context_size=1000)

        builder.add_section("Section 1", "Content 1")
        builder.add_section("Section 2", ["Line 1", "Line 2"])

        context = builder.build_context()

        assert "## Section 1" in context
        assert "Content 1" in context
        assert "## Section 2" in context
        assert "Line 1" in context
        assert "Line 2" in context

    def test_priority_ordering(self):
        """Test section ordering by priority"""
        builder = ContextBuilder(max_context_size=1000)

        builder.add_section("Low Priority", "Low content", priority=3)
        builder.add_section("High Priority", "High content", priority=1)
        builder.add_section("Medium Priority", "Medium content", priority=2)

        context = builder.build_context()

        # High priority should come first
        high_pos = context.find("## High Priority")
        medium_pos = context.find("## Medium Priority")
        low_pos = context.find("## Low Priority")

        assert high_pos < medium_pos < low_pos

    def test_size_limiting(self):
        """Test context size limiting"""
        builder = ContextBuilder(max_context_size=100)

        # Add content that would exceed the limit
        builder.add_section("Section 1", "A" * 50, priority=1)
        builder.add_section("Section 2", "B" * 50, priority=2)
        builder.add_section("Section 3", "C" * 50, priority=3)

        context = builder.build_context()

        # Should not exceed the limit
        assert len(context) <= 100

        # High priority section should be included
        assert "Section 1" in context

    def test_add_code_block(self):
        """Test adding code blocks"""
        builder = ContextBuilder()

        code = "def hello():\n    print('Hello, World!')"
        builder.add_code_block("Python Code", code, "python")

        context = builder.build_context()

        assert "```python" in context
        assert code in context
        assert "```" in context

    def test_add_list_items(self):
        """Test adding list items"""
        builder = ContextBuilder()

        items = ["Item 1", "Item 2", "Item 3"]
        builder.add_list_items("Todo List", items)

        context = builder.build_context()

        assert "- Item 1" in context
        assert "- Item 2" in context
        assert "- Item 3" in context

    def test_add_file_content(self):
        """Test adding file content"""
        builder = ContextBuilder()

        # Mock file reading
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = "File content"
            mock_open.return_value.__enter__.return_value = mock_file

            builder.add_file_content("File Section", "/path/to/file.txt")

            context = builder.build_context()
            assert "File content" in context

    def test_build_with_stats(self):
        """Test building context with statistics"""
        builder = ContextBuilder()

        builder.add_section("Test Section", "Test content")

        context = builder.build_context(include_stats=True)

        assert "Context Build Statistics" in context
        assert "Total sections:" in context
        assert "Included sections:" in context

    def test_get_stats(self):
        """Test getting context building statistics"""
        builder = ContextBuilder()

        builder.add_section("Test", "Content")
        builder.build_context()

        stats = builder.get_stats()
        assert stats.context_builds == 1
        assert stats.total_operations == 1

    def test_clear(self):
        """Test clearing context builder"""
        builder = ContextBuilder()

        builder.add_section("Test", "Content")
        builder.clear()

        context = builder.build_context()
        assert "Test" not in context


class TestStringTemplateEngine:
    """Test suite for StringTemplateEngine"""

    def test_register_and_render_template(self):
        """Test registering and rendering templates"""
        engine = StringTemplateEngine()

        engine.register_template("greeting", "Hello {name}, welcome to {place}!")

        result = engine.render_template(
            "greeting", {"name": "Alice", "place": "Wonderland"}
        )
        assert result == "Hello Alice, welcome to Wonderland!"

    def test_render_inline_template(self):
        """Test rendering inline templates"""
        engine = StringTemplateEngine()

        result = engine.render_inline("The answer is {answer}", {"answer": 42})
        assert result == "The answer is 42"

    def test_missing_template(self):
        """Test error handling for missing templates"""
        engine = StringTemplateEngine()

        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            engine.render_template("nonexistent", {})

    def test_missing_variable(self):
        """Test error handling for missing variables"""
        engine = StringTemplateEngine()

        engine.register_template("test", "Hello {name}")

        with pytest.raises(ValueError, match="Missing template variable"):
            engine.render_template("test", {})

    def test_get_templates(self):
        """Test getting list of registered templates"""
        engine = StringTemplateEngine()

        engine.register_template("template1", "Content 1")
        engine.register_template("template2", "Content 2")

        templates = engine.get_templates()
        assert "template1" in templates
        assert "template2" in templates
        assert len(templates) == 2

    def test_get_stats(self):
        """Test getting template rendering statistics"""
        engine = StringTemplateEngine()

        engine.register_template("test", "Hello {name}")
        engine.render_template("test", {"name": "World"})

        stats = engine.get_stats()
        assert stats.template_renders == 1
        assert stats.total_operations == 1


class TestStringOperationMonitor:
    """Test suite for StringOperationMonitor"""

    def test_monitor_operation(self):
        """Test monitoring string operations"""
        monitor = StringOperationMonitor()

        with monitor.monitor_operation("concatenation", "test_concat"):
            time.sleep(0.01)  # Simulate work

        stats = monitor.get_stats()
        assert stats.total_operations == 1
        assert stats.concatenations == 1
        assert stats.total_time_seconds > 0

    def test_operation_history(self):
        """Test operation history tracking"""
        monitor = StringOperationMonitor()

        with monitor.monitor_operation("template_render", "test_template"):
            pass

        history = monitor.get_operation_history()
        assert len(history) == 1
        assert history[0]["type"] == "template_render"
        assert history[0]["name"] == "test_template"
        assert "duration_ms" in history[0]
        assert "timestamp" in history[0]

    def test_performance_report(self):
        """Test generating performance reports"""
        monitor = StringOperationMonitor()

        with monitor.monitor_operation("concatenation"):
            pass

        report = monitor.get_performance_report()

        assert "String Operations Performance Report" in report
        assert "Total Operations: 1" in report
        assert "Concatenations: 1" in report

    def test_clear_stats(self):
        """Test clearing statistics"""
        monitor = StringOperationMonitor()

        with monitor.monitor_operation("concatenation"):
            pass

        assert monitor.get_stats().total_operations == 1

        monitor.clear_stats()
        assert monitor.get_stats().total_operations == 0


class TestGlobalFunctions:
    """Test suite for global convenience functions"""

    def test_get_string_monitor(self):
        """Test getting global string monitor"""
        monitor1 = get_string_monitor()
        monitor2 = get_string_monitor()

        # Should return the same instance (singleton)
        assert monitor1 is monitor2

    def test_get_template_engine(self):
        """Test getting global template engine"""
        engine1 = get_template_engine()
        engine2 = get_template_engine()

        # Should return the same instance (singleton)
        assert engine1 is engine2

    def test_optimized_join(self):
        """Test optimized string joining"""
        # Test empty list
        result = optimized_join([])
        assert result == ""

        # Test single item
        result = optimized_join(["single"])
        assert result == "single"

        # Test small list (uses built-in join)
        result = optimized_join(["a", "b", "c"], separator=",")
        assert result == "a,b,c"

        # Test large list (uses StringIO)
        large_list = [str(i) for i in range(200)]
        result = optimized_join(large_list, separator=",")
        expected = ",".join(large_list)
        assert result == expected

    def test_build_context_efficiently(self):
        """Test efficient context building"""
        sections = {"Section 1": "Content 1", "Section 2": ["Line 1", "Line 2"]}
        priorities = {"Section 1": 1, "Section 2": 2}

        context = build_context_efficiently(sections, priorities=priorities)

        assert "## Section 1" in context
        assert "Content 1" in context
        assert "## Section 2" in context
        assert "Line 1" in context

    def test_efficient_concatenate(self):
        """Test efficient concatenation"""
        result = efficient_concatenate("Hello", " ", "World", "!")
        assert result == "Hello World!"

    def test_efficient_format(self):
        """Test efficient formatting"""
        result = efficient_format("Hello {name}, age {age}", name="Alice", age=30)
        assert result == "Hello Alice, age 30"


if __name__ == "__main__":
    pytest.main([__file__])
