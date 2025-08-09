"""
Standardized Error Handler for EQUITR Coder

This module provides consistent error handling patterns across the codebase,
including contextual error messages, recovery suggestions, and error correlation.

Features:
- Consistent error handling patterns
- Contextual error messages with specific details
- Error recovery suggestion system
- Error correlation and tracking capabilities
- Structured error logging
- Error escalation for critical failures
"""

import logging
import traceback
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
# import inspect  # Unused
# import sys  # Unused

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    MODEL = "model"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    RESOURCE = "resource"
    LOGIC = "logic"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


@dataclass
class ContextualError:
    """Enhanced error with context and recovery suggestions"""
    error_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


@dataclass
class HandledError:
    """Result of error handling with context and suggestions"""
    original_error: Exception
    contextual_error: ContextualError
    handled: bool = False
    escalated: bool = False


@dataclass
class RecoveryAction:
    """Suggested recovery action for an error"""
    action_type: str
    description: str
    automated: bool = False
    action_function: Optional[Callable] = None


@dataclass
class EscalationResult:
    """Result of error escalation"""
    escalated: bool
    escalation_level: str
    notification_sent: bool = False


class StandardizedErrorHandler:
    """
    Standardized error handler that provides consistent error patterns,
    contextual messages, recovery suggestions, and error tracking.
    """
    
    def __init__(self, 
                 enable_correlation: bool = True,
                 enable_recovery_suggestions: bool = True,
                 max_error_history: int = 1000):
        """
        Initialize the standardized error handler
        
        Args:
            enable_correlation: Enable error correlation tracking
            enable_recovery_suggestions: Enable automatic recovery suggestions
            max_error_history: Maximum number of errors to keep in history
        """
        self.enable_correlation = enable_correlation
        self.enable_recovery_suggestions = enable_recovery_suggestions
        
        # Error tracking
        self._error_history: deque = deque(maxlen=max_error_history)
        self._error_counts: Dict[str, int] = {}
        self._correlation_map: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        
        # Recovery actions registry
        self._recovery_actions: Dict[ErrorCategory, List[RecoveryAction]] = {
            ErrorCategory.CONFIGURATION: [
                RecoveryAction("check_config", "Check configuration file syntax and values"),
                RecoveryAction("reset_config", "Reset to default configuration", automated=True),
                RecoveryAction("validate_schema", "Validate configuration against schema")
            ],
            ErrorCategory.AUTHENTICATION: [
                RecoveryAction("check_api_keys", "Verify API keys are set and valid"),
                RecoveryAction("refresh_tokens", "Refresh authentication tokens"),
                RecoveryAction("check_permissions", "Verify account permissions")
            ],
            ErrorCategory.NETWORK: [
                RecoveryAction("retry_request", "Retry the network request", automated=True),
                RecoveryAction("check_connectivity", "Check internet connectivity"),
                RecoveryAction("use_fallback", "Use fallback service if available")
            ],
            ErrorCategory.FILE_SYSTEM: [
                RecoveryAction("check_permissions", "Check file/directory permissions"),
                RecoveryAction("create_directory", "Create missing directories", automated=True),
                RecoveryAction("check_disk_space", "Check available disk space")
            ],
            ErrorCategory.MODEL: [
                RecoveryAction("validate_model", "Validate model name and availability"),
                RecoveryAction("use_fallback_model", "Use fallback model", automated=True),
                RecoveryAction("check_model_limits", "Check model usage limits")
            ],
            ErrorCategory.VALIDATION: [
                RecoveryAction("check_input", "Check input data format and values"),
                RecoveryAction("validate_schema", "Validate data against expected schema"),
                RecoveryAction("fix_data_types", "Fix data type mismatches")
            ]
        }
        
        logger.info("StandardizedErrorHandler initialized")
    
    def handle_error(self, 
                    error: Exception,
                    context: Optional[Dict[str, Any]] = None,
                    correlation_id: Optional[str] = None,
                    category: Optional[ErrorCategory] = None,
                    severity: Optional[ErrorSeverity] = None) -> HandledError:
        """
        Handle an error with context and recovery suggestions
        
        Args:
            error: The original exception
            context: Additional context information
            correlation_id: Correlation ID for tracking related errors
            category: Error category (auto-detected if not provided)
            severity: Error severity (auto-detected if not provided)
            
        Returns:
            HandledError with context and suggestions
        """
        with self._lock:
            # Generate error ID
            error_id = self._generate_error_id(error)
            
            # Auto-detect category and severity if not provided
            if category is None:
                category = self._categorize_error(error)
            
            if severity is None:
                severity = self._assess_severity(error, category)
            
            # Create contextual error
            contextual_error = ContextualError(
                error_id=error_id,
                message=self._format_error_message(error, context),
                category=category,
                severity=severity,
                context=context or {},
                stack_trace=self._get_stack_trace(error),
                recovery_suggestions=self._get_recovery_suggestions(error, category),
                correlation_id=correlation_id
            )
            
            # Create handled error result
            handled_error = HandledError(
                original_error=error,
                contextual_error=contextual_error,
                handled=True
            )
            
            # Track error
            self._track_error(contextual_error)
            
            # Log error
            self._log_error(contextual_error)
            
            # Check for escalation
            if self._should_escalate(contextual_error):
                escalation_result = self._escalate_error(contextual_error)
                handled_error.escalated = escalation_result.escalated
            
            return handled_error
    
    def create_contextual_exception(self, 
                                  message: str,
                                  category: ErrorCategory,
                                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                                  context: Optional[Dict[str, Any]] = None,
                                  recovery_suggestions: Optional[List[str]] = None) -> Exception:
        """
        Create a contextual exception with enhanced information
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            context: Additional context
            recovery_suggestions: Custom recovery suggestions
            
        Returns:
            Enhanced exception with context
        """
        error_id = self._generate_error_id_from_message(message)
        
        contextual_error = ContextualError(
            error_id=error_id,
            message=message,
            category=category,
            severity=severity,
            context=context or {},
            recovery_suggestions=recovery_suggestions or self._get_recovery_suggestions_by_category(category)
        )
        
        # Create custom exception class with context
        class ContextualException(Exception):
            def __init__(self, contextual_error: ContextualError):
                self.contextual_error = contextual_error
                super().__init__(contextual_error.message)
        
        return ContextualException(contextual_error)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics and trends
        
        Returns:
            Dictionary with error statistics
        """
        with self._lock:
            total_errors = len(self._error_history)
            
            # Category breakdown
            category_counts: Dict[str, int] = {}
            severity_counts: Dict[str, int] = {}
            
            for error in self._error_history:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Recent errors (last hour)
            recent_cutoff = datetime.now().timestamp() - 3600
            recent_errors = [e for e in self._error_history if e.timestamp.timestamp() > recent_cutoff]
            
            return {
                'total_errors': total_errors,
                'recent_errors_count': len(recent_errors),
                'category_breakdown': category_counts,
                'severity_breakdown': severity_counts,
                'most_common_errors': dict(sorted(self._error_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'correlation_groups': len(self._correlation_map)
            }
    
    def get_recovery_suggestions(self, error: Exception) -> List[str]:
        """
        Get recovery suggestions for a specific error
        
        Args:
            error: The exception to get suggestions for
            
        Returns:
            List of recovery suggestions
        """
        category = self._categorize_error(error)
        return self._get_recovery_suggestions(error, category)
    
    def clear_error_history(self) -> None:
        """
        Clear error history and statistics
        """
        with self._lock:
            self._error_history.clear()
            self._error_counts.clear()
            self._correlation_map.clear()
            logger.info("Error history cleared")
    
    def _generate_error_id(self, error: Exception) -> str:
        """
        Generate unique error ID based on error type and message
        """
        error_type = type(error).__name__
        error_msg = str(error)[:100]  # Truncate long messages
        return f"{error_type}_{hash(error_msg) % 10000:04d}"
    
    def _generate_error_id_from_message(self, message: str) -> str:
        """
        Generate error ID from message
        """
        return f"CUSTOM_{hash(message) % 10000:04d}"
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Automatically categorize error based on type and message
        """
        error_type = type(error).__name__.lower()
        error_msg = str(error).lower()
        
        # Configuration errors
        if any(keyword in error_msg for keyword in ['config', 'setting', 'parameter', 'yaml', 'json']):
            return ErrorCategory.CONFIGURATION
        
        # Authentication errors
        if any(keyword in error_msg for keyword in ['api key', 'token', 'auth', 'credential', 'unauthorized']):
            return ErrorCategory.AUTHENTICATION
        
        # Network errors
        if any(keyword in error_type for keyword in ['connection', 'timeout', 'network', 'http']):
            return ErrorCategory.NETWORK
        
        # File system errors
        if any(keyword in error_type for keyword in ['file', 'directory', 'path', 'permission']):
            return ErrorCategory.FILE_SYSTEM
        
        # Model errors
        if any(keyword in error_msg for keyword in ['model', 'llm', 'openai', 'anthropic']):
            return ErrorCategory.MODEL
        
        # Validation errors
        if any(keyword in error_type for keyword in ['validation', 'value', 'type']):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """
        Assess error severity based on type and category
        """
        error_type = type(error).__name__.lower()
        
        # Critical errors
        if any(keyword in error_type for keyword in ['system', 'memory', 'fatal']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.NETWORK, ErrorCategory.MODEL]:
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _format_error_message(self, error: Exception, context: Optional[Dict[str, Any]]) -> str:
        """
        Format error message with context
        """
        base_message = str(error)
        
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            return f"{base_message} (Context: {context_str})"
        
        return base_message
    
    def _get_stack_trace(self, error: Exception) -> str:
        """
        Get formatted stack trace for error
        """
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    def _get_recovery_suggestions(self, error: Exception, category: ErrorCategory) -> List[str]:
        """
        Get recovery suggestions based on error and category
        """
        if not self.enable_recovery_suggestions:
            return []
        
        suggestions = self._get_recovery_suggestions_by_category(category)
        
        # Add specific suggestions based on error message
        error_msg = str(error).lower()
        
        if 'api key' in error_msg:
            suggestions.append("Set the required API key in environment variables")
        
        if 'file not found' in error_msg:
            suggestions.append("Check if the file path is correct and the file exists")
        
        if 'permission denied' in error_msg:
            suggestions.append("Check file/directory permissions")
        
        if 'connection' in error_msg:
            suggestions.append("Check internet connectivity and try again")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _get_recovery_suggestions_by_category(self, category: ErrorCategory) -> List[str]:
        """
        Get recovery suggestions for a specific category
        """
        actions = self._recovery_actions.get(category, [])
        return [action.description for action in actions]
    
    def _track_error(self, error: ContextualError) -> None:
        """
        Track error for statistics and correlation
        """
        # Add to history
        self._error_history.append(error)
        
        # Update counts
        error_key = f"{error.category.value}_{error.message[:50]}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Handle correlation
        if self.enable_correlation and error.correlation_id:
            if error.correlation_id not in self._correlation_map:
                self._correlation_map[error.correlation_id] = []
            self._correlation_map[error.correlation_id].append(error.error_id)
    
    def _log_error(self, error: ContextualError) -> None:
        """
        Log error with appropriate level and context
        """
        log_data = {
            'error_id': error.error_id,
            'category': error.category.value,
            'severity': error.severity.value,
            'context': error.context,
            'recovery_suggestions': error.recovery_suggestions
        }
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {error.message}", extra=log_data)
    
    def _should_escalate(self, error: ContextualError) -> bool:
        """
        Determine if error should be escalated
        """
        # Always escalate critical errors
        if error.severity == ErrorSeverity.CRITICAL:
            return True
        
        # Escalate if same error occurs frequently
        error_key = f"{error.category.value}_{error.message[:50]}"
        if self._error_counts.get(error_key, 0) > 5:
            return True
        
        return False
    
    def _escalate_error(self, error: ContextualError) -> EscalationResult:
        """
        Escalate error to appropriate level
        """
        escalation_level = "high" if error.severity == ErrorSeverity.CRITICAL else "medium"
        
        logger.critical(f"ESCALATED ERROR [{escalation_level.upper()}]: {error.message}", 
                       extra={'error_id': error.error_id, 'escalation_level': escalation_level})
        
        return EscalationResult(
            escalated=True,
            escalation_level=escalation_level,
            notification_sent=True
        )


# Global error handler instance
_global_error_handler: Optional[StandardizedErrorHandler] = None
_handler_lock = threading.Lock()


def get_error_handler() -> StandardizedErrorHandler:
    """Get the global error handler instance"""
    global _global_error_handler
    
    if _global_error_handler is None:
        with _handler_lock:
            if _global_error_handler is None:
                _global_error_handler = StandardizedErrorHandler()
    
    return _global_error_handler


def configure_error_handler(handler: StandardizedErrorHandler) -> None:
    """Configure the global error handler"""
    global _global_error_handler
    
    with _handler_lock:
        _global_error_handler = handler


def handle_error(error: Exception, 
                context: Optional[Dict[str, Any]] = None,
                correlation_id: Optional[str] = None,
                category: Optional[ErrorCategory] = None,
                severity: Optional[ErrorSeverity] = None) -> HandledError:
    """Handle error using global error handler"""
    handler = get_error_handler()
    return handler.handle_error(error, context, correlation_id, category, severity)


def create_contextual_exception(message: str,
                              category: ErrorCategory,
                              severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                              context: Optional[Dict[str, Any]] = None,
                              recovery_suggestions: Optional[List[str]] = None) -> Exception:
    """Create contextual exception using global error handler"""
    handler = get_error_handler()
    return handler.create_contextual_exception(message, category, severity, context, recovery_suggestions)


# Decorator for automatic error handling
def handle_errors(category: Optional[ErrorCategory] = None,
                 severity: Optional[ErrorSeverity] = None,
                 context_extractor: Optional[Callable] = None):
    """
    Decorator for automatic error handling
    
    Args:
        category: Error category to assign
        severity: Error severity to assign
        context_extractor: Function to extract context from function args
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract context if extractor provided
                context = None
                if context_extractor:
                    try:
                        context = context_extractor(*args, **kwargs)
                    except Exception:
                        pass
                
                # Handle the error
                _ = handle_error(e, context, category=category, severity=severity)
                
                # Re-raise the original exception
                raise e
        
        return wrapper
    return decorator