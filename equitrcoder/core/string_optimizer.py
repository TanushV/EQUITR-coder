"""
String Operations Optimizer for EQUITR Coder

This module provides optimized string operations and context building
to improve performance and reduce memory usage.

Features:
- Efficient string concatenation using StringIO
- Optimized context building for large text operations
- String operation performance monitoring
- Memory-efficient string processing
- Template-based string generation
"""

import io
import logging
import threading
import time

# import weakref  # Unused
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class StringOperationStats:
    """Statistics for string operations"""

    total_operations: int = 0
    total_time_seconds: float = 0.0
    total_memory_bytes: int = 0
    concatenations: int = 0
    context_builds: int = 0
    template_renders: int = 0

    @property
    def average_time_ms(self) -> float:
        """Average operation time in milliseconds"""
        if self.total_operations == 0:
            return 0.0
        return (self.total_time_seconds / self.total_operations) * 1000

    @property
    def average_memory_kb(self) -> float:
        """Average memory usage in KB"""
        if self.total_operations == 0:
            return 0.0
        return (self.total_memory_bytes / self.total_operations) / 1024


class OptimizedStringBuilder:
    """
    Memory-efficient string builder using StringIO for large concatenations
    """

    def __init__(self, initial_capacity: int = 1024):
        """
        Initialize the string builder

        Args:
            initial_capacity: Initial buffer capacity hint
        """
        self._buffer = io.StringIO()
        self._length = 0
        self._initial_capacity = initial_capacity

    def append(self, text: Union[str, Any]) -> "OptimizedStringBuilder":
        """
        Append text to the builder

        Args:
            text: Text to append (will be converted to string)

        Returns:
            Self for method chaining
        """
        if text is not None:
            text_str = str(text)
            self._buffer.write(text_str)
            self._length += len(text_str)
        return self

    def append_line(self, text: Union[str, Any] = "") -> "OptimizedStringBuilder":
        """
        Append text with a newline

        Args:
            text: Text to append

        Returns:
            Self for method chaining
        """
        return self.append(text).append("\n")

    def append_lines(self, lines: List[Union[str, Any]]) -> "OptimizedStringBuilder":
        """
        Append multiple lines

        Args:
            lines: List of lines to append

        Returns:
            Self for method chaining
        """
        for line in lines:
            self.append_line(line)
        return self

    def append_separator(
        self, separator: str = "-", length: int = 50
    ) -> "OptimizedStringBuilder":
        """
        Append a separator line

        Args:
            separator: Character to use for separator
            length: Length of separator line

        Returns:
            Self for method chaining
        """
        return self.append_line(separator * length)

    def append_formatted(self, template: str, **kwargs) -> "OptimizedStringBuilder":
        """
        Append formatted text using template

        Args:
            template: Format template
            **kwargs: Template variables

        Returns:
            Self for method chaining
        """
        formatted_text = template.format(**kwargs)
        return self.append(formatted_text)

    def append_indented(self, text: str, indent: int = 4) -> "OptimizedStringBuilder":
        """
        Append text with indentation

        Args:
            text: Text to append
            indent: Number of spaces to indent

        Returns:
            Self for method chaining
        """
        indent_str = " " * indent
        indented_lines = [indent_str + line for line in text.split("\n")]
        return self.append("\n".join(indented_lines))

    def clear(self) -> "OptimizedStringBuilder":
        """
        Clear the buffer

        Returns:
            Self for method chaining
        """
        self._buffer.close()
        self._buffer = io.StringIO()
        self._length = 0
        return self

    def to_string(self) -> str:
        """
        Get the final string

        Returns:
            Built string
        """
        return self._buffer.getvalue()

    def __len__(self) -> int:
        """Get current length of built string"""
        return self._length

    def __str__(self) -> str:
        """String representation"""
        return self.to_string()

    def __enter__(self) -> "OptimizedStringBuilder":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._buffer.close()


class ContextBuilder:
    """
    Optimized context builder for large text operations
    """

    def __init__(self, max_context_size: int = 100000):
        """
        Initialize context builder

        Args:
            max_context_size: Maximum context size in characters
        """
        self.max_context_size = max_context_size
        self._sections: Dict[str, List[str]] = {}
        self._priorities: Dict[str, int] = {}
        self._stats = StringOperationStats()

    def add_section(
        self, name: str, content: Union[str, List[str]], priority: int = 1
    ) -> None:
        """
        Add a section to the context

        Args:
            name: Section name
            content: Section content (string or list of strings)
            priority: Section priority (1=high, 2=medium, 3=low)
        """
        if isinstance(content, str):
            content = [content]

        self._sections[name] = content
        self._priorities[name] = priority

    def add_file_content(self, name: str, file_path: str, priority: int = 2) -> None:
        """
        Add file content as a section

        Args:
            name: Section name
            file_path: Path to file
            priority: Section priority
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.add_section(name, content, priority)
        except Exception as e:
            logger.warning(f"Failed to add file content {file_path}: {e}")

    def add_code_block(
        self, name: str, code: str, language: str = "python", priority: int = 2
    ) -> None:
        """
        Add code block with syntax highlighting markers

        Args:
            name: Section name
            code: Code content
            language: Programming language
            priority: Section priority
        """
        formatted_code = f"```{language}\n{code}\n```"
        self.add_section(name, formatted_code, priority)

    def add_list_items(
        self, name: str, items: List[str], bullet: str = "- ", priority: int = 2
    ) -> None:
        """
        Add list items as a section

        Args:
            name: Section name
            items: List items
            bullet: Bullet character/string
            priority: Section priority
        """
        formatted_items = [f"{bullet}{item}" for item in items]
        self.add_section(name, formatted_items, priority)

    def build_context(self, include_stats: bool = False) -> str:
        """
        Build the final context string with size optimization

        Args:
            include_stats: Whether to include build statistics

        Returns:
            Optimized context string
        """
        start_time = time.time()

        with OptimizedStringBuilder() as builder:
            # Sort sections by priority
            sorted_sections = sorted(
                self._sections.items(), key=lambda x: self._priorities.get(x[0], 2)
            )

            current_size = 0
            included_sections = []

            for section_name, content_lines in sorted_sections:
                # Calculate section size
                section_content = "\n".join(content_lines)
                section_size = (
                    len(section_content) + len(section_name) + 10
                )  # Header overhead

                # Check if adding this section would exceed limit
                if current_size + section_size > self.max_context_size:
                    # Try to include partial content for high-priority sections
                    if self._priorities.get(section_name, 2) == 1:
                        remaining_space = (
                            self.max_context_size
                            - current_size
                            - len(section_name)
                            - 50
                        )
                        if remaining_space > 100:  # Minimum useful content size
                            truncated_content = (
                                section_content[:remaining_space] + "...[truncated]"
                            )
                            builder.append_line(f"## {section_name}")
                            builder.append_line(truncated_content)
                            builder.append_line()
                            included_sections.append(f"{section_name} (truncated)")
                    break

                # Add full section
                builder.append_line(f"## {section_name}")
                for line in content_lines:
                    builder.append_line(line)
                builder.append_line()

                current_size += section_size
                included_sections.append(section_name)

            # Add statistics if requested
            if include_stats:
                builder.append_separator("=")
                builder.append_line("## Context Build Statistics")
                builder.append_line(f"Total sections: {len(self._sections)}")
                builder.append_line(f"Included sections: {len(included_sections)}")
                builder.append_line(f"Final size: {current_size} characters")
                builder.append_line(f"Size limit: {self.max_context_size} characters")
                builder.append_line(f"Included: {', '.join(included_sections)}")

            result = builder.to_string()

        # Update statistics
        end_time = time.time()
        self._stats.total_operations += 1
        self._stats.context_builds += 1
        self._stats.total_time_seconds += end_time - start_time
        self._stats.total_memory_bytes += len(result.encode("utf-8"))

        return result

    def get_stats(self) -> StringOperationStats:
        """Get context building statistics"""
        return StringOperationStats(
            total_operations=self._stats.total_operations,
            total_time_seconds=self._stats.total_time_seconds,
            total_memory_bytes=self._stats.total_memory_bytes,
            context_builds=self._stats.context_builds,
        )

    def clear(self) -> None:
        """Clear all sections"""
        self._sections.clear()
        self._priorities.clear()


class StringTemplateEngine:
    """
    Optimized template engine for string generation
    """

    def __init__(self):
        self._templates: Dict[str, str] = {}
        self._compiled_templates: Dict[str, Any] = {}
        self._stats = StringOperationStats()

    def register_template(self, name: str, template: str) -> None:
        """
        Register a template

        Args:
            name: Template name
            template: Template string with {variable} placeholders
        """
        self._templates[name] = template
        # Pre-compile template for faster rendering
        self._compiled_templates[name] = template

    def render_template(self, name: str, variables: Dict[str, Any]) -> str:
        """
        Render a template with variables

        Args:
            name: Template name
            variables: Template variables

        Returns:
            Rendered string
        """
        start_time = time.time()

        if name not in self._templates:
            raise ValueError(f"Template '{name}' not found")

        template = self._templates[name]

        try:
            result = template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

        # Update statistics
        end_time = time.time()
        self._stats.total_operations += 1
        self._stats.template_renders += 1
        self._stats.total_time_seconds += end_time - start_time
        self._stats.total_memory_bytes += len(result.encode("utf-8"))

        return result

    def render_inline(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render an inline template

        Args:
            template: Template string
            variables: Template variables

        Returns:
            Rendered string
        """
        start_time = time.time()

        try:
            result = template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

        # Update statistics
        end_time = time.time()
        self._stats.total_operations += 1
        self._stats.template_renders += 1
        self._stats.total_time_seconds += end_time - start_time
        self._stats.total_memory_bytes += len(result.encode("utf-8"))

        return result

    def get_templates(self) -> List[str]:
        """Get list of registered template names"""
        return list(self._templates.keys())

    def get_stats(self) -> StringOperationStats:
        """Get template rendering statistics"""
        return StringOperationStats(
            total_operations=self._stats.total_operations,
            total_time_seconds=self._stats.total_time_seconds,
            total_memory_bytes=self._stats.total_memory_bytes,
            template_renders=self._stats.template_renders,
        )


from .interfaces import IMonitor  # noqa: E402


class StringOperationMonitor(IMonitor):
    """
    Monitor and optimize string operations across the application
    """

    def __init__(self):
        self._stats = StringOperationStats()
        self._lock = threading.RLock()
        self._operation_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    @contextmanager
    def monitor_operation(self, operation_type: str, operation_name: str = ""):
        """
        Context manager to monitor string operations

        Args:
            operation_type: Type of operation (concatenation, context_build, template_render)
            operation_name: Optional operation name for tracking
        """
        start_time = time.time()
        # start_memory = 0  # Would need memory profiling for accurate measurement

        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time

            with self._lock:
                self._stats.total_operations += 1
                self._stats.total_time_seconds += duration

                if operation_type == "concatenation":
                    self._stats.concatenations += 1
                elif operation_type == "context_build":
                    self._stats.context_builds += 1
                elif operation_type == "template_render":
                    self._stats.template_renders += 1

                # Record operation history
                operation_record = {
                    "type": operation_type,
                    "name": operation_name,
                    "duration_ms": duration * 1000,
                    "timestamp": datetime.now().isoformat(),
                }

                self._operation_history.append(operation_record)

                # Limit history size
                if len(self._operation_history) > self._max_history:
                    self._operation_history = self._operation_history[
                        -self._max_history :
                    ]

    def get_stats(self) -> StringOperationStats:
        """Get comprehensive string operation statistics"""
        with self._lock:
            return StringOperationStats(
                total_operations=self._stats.total_operations,
                total_time_seconds=self._stats.total_time_seconds,
                total_memory_bytes=self._stats.total_memory_bytes,
                concatenations=self._stats.concatenations,
                context_builds=self._stats.context_builds,
                template_renders=self._stats.template_renders,
            )

    def get_operation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent operation history"""
        with self._lock:
            return self._operation_history[-limit:]

    def get_performance_report(self) -> str:
        """Generate a performance report"""
        stats = self.get_stats()

        with OptimizedStringBuilder() as builder:
            builder.append_line("String Operations Performance Report")
            builder.append_separator("=")
            builder.append_line(f"Total Operations: {stats.total_operations}")
            builder.append_line(f"Total Time: {stats.total_time_seconds:.3f}s")
            builder.append_line(f"Average Time: {stats.average_time_ms:.2f}ms")
            builder.append_line(f"Average Memory: {stats.average_memory_kb:.2f}KB")
            builder.append_line()
            builder.append_line("Operation Breakdown:")
            builder.append_line(f"  Concatenations: {stats.concatenations}")
            builder.append_line(f"  Context Builds: {stats.context_builds}")
            builder.append_line(f"  Template Renders: {stats.template_renders}")

            return builder.to_string()

    def clear_stats(self) -> None:
        """Clear all statistics and history"""
        with self._lock:
            self._stats = StringOperationStats()
            self._operation_history.clear()

    # IMonitor interface implementation
    def start_monitoring(self) -> None:
        """Start monitoring (already active by default)"""
        logger.info("String operation monitoring started")

    def stop_monitoring(self) -> None:
        """Stop monitoring"""
        logger.info("String operation monitoring stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics (IMonitor interface)"""
        stats = self.get_stats()
        return {
            "total_operations": stats.total_operations,
            "total_time_seconds": stats.total_time_seconds,
            "average_time_ms": stats.average_time_ms,
            "total_memory_bytes": stats.total_memory_bytes,
            "average_memory_kb": stats.average_memory_kb,
            "concatenations": stats.concatenations,
            "context_builds": stats.context_builds,
            "template_renders": stats.template_renders,
            "operation_history_count": len(self._operation_history),
        }

    def reset_metrics(self) -> None:
        """Reset all metrics (IMonitor interface)"""
        self.clear_stats()


# Global instances
_string_monitor: Optional[StringOperationMonitor] = None
_template_engine: Optional[StringTemplateEngine] = None
_monitor_lock = threading.Lock()


def get_string_monitor() -> StringOperationMonitor:
    """Get the global string operation monitor"""
    global _string_monitor

    if _string_monitor is None:
        with _monitor_lock:
            if _string_monitor is None:
                _string_monitor = StringOperationMonitor()

    return _string_monitor


def get_template_engine() -> StringTemplateEngine:
    """Get the global template engine"""
    global _template_engine

    if _template_engine is None:
        with _monitor_lock:
            if _template_engine is None:
                _template_engine = StringTemplateEngine()

    return _template_engine


def optimized_join(items: List[str], separator: str = "") -> str:
    """
    Optimized string joining using StringIO for large lists

    Args:
        items: List of strings to join
        separator: Separator string

    Returns:
        Joined string
    """
    monitor = get_string_monitor()

    with monitor.monitor_operation("concatenation", "optimized_join"):
        if not items:
            return ""

        if len(items) == 1:
            return items[0]

        # Use built-in join for small lists (it's optimized in CPython)
        if len(items) < 100:
            return separator.join(items)

        # Use StringIO for large lists
        with OptimizedStringBuilder() as builder:
            for i, item in enumerate(items):
                if i > 0:
                    builder.append(separator)
                builder.append(item)

            return builder.to_string()


def build_context_efficiently(
    sections: Dict[str, Union[str, List[str]]],
    max_size: int = 100000,
    priorities: Optional[Dict[str, int]] = None,
) -> str:
    """
    Efficiently build context from multiple sections

    Args:
        sections: Dictionary of section name to content
        max_size: Maximum context size
        priorities: Optional section priorities

    Returns:
        Built context string
    """
    monitor = get_string_monitor()

    with monitor.monitor_operation("context_build", "build_context_efficiently"):
        builder = ContextBuilder(max_size)

        for name, content in sections.items():
            priority = priorities.get(name, 2) if priorities else 2
            builder.add_section(name, content, priority)

        return builder.build_context()


# Convenience functions for common string operations
def efficient_concatenate(*args) -> str:
    """Efficiently concatenate multiple strings"""
    return optimized_join([str(arg) for arg in args])


def efficient_format(template: str, **kwargs) -> str:
    """Efficiently format a template string"""
    engine = get_template_engine()
    return engine.render_inline(template, kwargs)
