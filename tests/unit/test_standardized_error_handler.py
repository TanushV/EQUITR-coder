"""
Unit tests for Standardized Error Handler

Tests the error handling system including:
- Error categorization and severity assessment
- Contextual error creation
- Recovery suggestions
- Error tracking and correlation
- Error escalation
"""

import pytest
import threading
from datetime import datetime

from equitrcoder.core.standardized_error_handler import (
    StandardizedErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ContextualError,
    HandledError,
    RecoveryAction,
    EscalationResult,
    get_error_handler,
    configure_error_handler,
    handle_error,
    create_contextual_exception,
    handle_errors
)


class TestStandardizedErrorHandler:
    """Test suite for StandardizedErrorHandler"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.handler = StandardizedErrorHandler()
    
    def test_handler_initialization(self):
        """Test handler initialization"""
        assert isinstance(self.handler, StandardizedErrorHandler)
        assert self.handler.enable_correlation is True
        assert self.handler.enable_recovery_suggestions is True
        assert len(self.handler._recovery_actions) > 0
    
    def test_error_categorization(self):
        """Test automatic error categorization"""
        # Configuration error
        config_error = ValueError("Invalid config parameter")
        category = self.handler._categorize_error(config_error)
        assert category == ErrorCategory.CONFIGURATION
        
        # Authentication error
        auth_error = Exception("API key not found")
        category = self.handler._categorize_error(auth_error)
        assert category == ErrorCategory.AUTHENTICATION
        
        # File system error
        file_error = FileNotFoundError("File not found")
        category = self.handler._categorize_error(file_error)
        assert category == ErrorCategory.FILE_SYSTEM
        
        # Network error
        network_error = ConnectionError("Connection failed")
        category = self.handler._categorize_error(network_error)
        assert category == ErrorCategory.NETWORK
    
    def test_severity_assessment(self):
        """Test error severity assessment"""
        # Critical error
        critical_error = SystemError("System failure")
        severity = self.handler._assess_severity(critical_error, ErrorCategory.UNKNOWN)
        assert severity == ErrorSeverity.CRITICAL
        
        # High severity error
        auth_error = Exception("Authentication failed")
        severity = self.handler._assess_severity(auth_error, ErrorCategory.AUTHENTICATION)
        assert severity == ErrorSeverity.HIGH
        
        # Medium severity error
        network_error = Exception("Network timeout")
        severity = self.handler._assess_severity(network_error, ErrorCategory.NETWORK)
        assert severity == ErrorSeverity.MEDIUM
    
    def test_handle_error(self):
        """Test error handling"""
        error = ValueError("Test error")
        context = {"operation": "test", "user": "test_user"}
        
        handled_error = self.handler.handle_error(error, context=context)
        
        assert isinstance(handled_error, HandledError)
        assert handled_error.original_error is error
        assert handled_error.handled is True
        assert handled_error.contextual_error.context == context
        assert len(handled_error.contextual_error.recovery_suggestions) > 0
    
    def test_contextual_error_creation(self):
        """Test contextual error creation"""
        message = "Test contextual error"
        category = ErrorCategory.VALIDATION
        severity = ErrorSeverity.HIGH
        context = {"field": "test_field"}
        
        contextual_error = ContextualError(
            error_id="TEST_001",
            message=message,
            category=category,
            severity=severity,
            context=context
        )
        
        assert contextual_error.message == message
        assert contextual_error.category == category
        assert contextual_error.severity == severity
        assert contextual_error.context == context
        assert isinstance(contextual_error.timestamp, datetime)
    
    def test_recovery_suggestions(self):
        """Test recovery suggestions generation"""
        # Configuration error
        config_error = ValueError("Invalid configuration")
        suggestions = self.handler.get_recovery_suggestions(config_error)
        
        assert len(suggestions) > 0
        assert any("config" in suggestion.lower() for suggestion in suggestions)
        
        # Authentication error
        auth_error = Exception("API key missing")
        suggestions = self.handler.get_recovery_suggestions(auth_error)
        
        assert len(suggestions) > 0
        assert any("api key" in suggestion.lower() for suggestion in suggestions)
    
    def test_error_tracking(self):
        """Test error tracking and statistics"""
        # Handle multiple errors
        for i in range(5):
            error = ValueError(f"Test error {i}")
            self.handler.handle_error(error)
        
        stats = self.handler.get_error_statistics()
        
        assert stats['total_errors'] == 5
        assert 'category_breakdown' in stats
        assert 'severity_breakdown' in stats
        assert 'most_common_errors' in stats
    
    def test_error_correlation(self):
        """Test error correlation tracking"""
        correlation_id = "test_correlation_123"
        
        # Handle correlated errors
        error1 = ValueError("First error")
        error2 = RuntimeError("Second error")
        
        self.handler.handle_error(error1, correlation_id=correlation_id)
        self.handler.handle_error(error2, correlation_id=correlation_id)
        
        stats = self.handler.get_error_statistics()
        assert stats['correlation_groups'] > 0
    
    def test_error_escalation(self):
        """Test error escalation"""
        # Critical error should escalate
        critical_error = SystemError("Critical system failure")
        handled_error = self.handler.handle_error(critical_error)
        
        # Check if escalation logic is triggered (would be True for critical errors)
        should_escalate = self.handler._should_escalate(handled_error.contextual_error)
        assert should_escalate is True
    
    def test_create_contextual_exception(self):
        """Test contextual exception creation"""
        message = "Test contextual exception"
        category = ErrorCategory.VALIDATION
        severity = ErrorSeverity.HIGH
        context = {"field": "test"}
        
        exception = self.handler.create_contextual_exception(
            message, category, severity, context
        )
        
        assert isinstance(exception, Exception)
        assert str(exception) == message
        assert hasattr(exception, 'contextual_error')
        assert exception.contextual_error.category == category
        assert exception.contextual_error.severity == severity
    
    def test_clear_error_history(self):
        """Test clearing error history"""
        # Add some errors
        for i in range(3):
            error = ValueError(f"Test error {i}")
            self.handler.handle_error(error)
        
        # Verify errors exist
        stats = self.handler.get_error_statistics()
        assert stats['total_errors'] == 3
        
        # Clear history
        self.handler.clear_error_history()
        
        # Verify history is cleared
        stats = self.handler.get_error_statistics()
        assert stats['total_errors'] == 0
    
    def test_thread_safety(self):
        """Test thread safety of error handler"""
        errors = []
        
        def handle_errors_in_thread():
            for i in range(10):
                try:
                    error = ValueError(f"Thread error {i}")
                    handled_error = self.handler.handle_error(error)
                    errors.append(handled_error)
                except Exception as e:
                    errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=handle_errors_in_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 50  # 5 threads * 10 errors each
        assert all(isinstance(error, HandledError) for error in errors)


class TestGlobalErrorHandler:
    """Test suite for global error handler functions"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Reset global handler
        import equitrcoder.core.standardized_error_handler
        equitrcoder.core.standardized_error_handler._global_error_handler = None
    
    def test_get_error_handler(self):
        """Test getting global error handler"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2
        assert isinstance(handler1, StandardizedErrorHandler)
    
    def test_configure_error_handler(self):
        """Test configuring global error handler"""
        custom_handler = StandardizedErrorHandler(enable_correlation=False)
        configure_error_handler(custom_handler)
        
        global_handler = get_error_handler()
        assert global_handler is custom_handler
        assert global_handler.enable_correlation is False
    
    def test_global_handle_error(self):
        """Test global handle_error function"""
        error = ValueError("Global test error")
        context = {"test": "global"}
        
        handled_error = handle_error(error, context=context)
        
        assert isinstance(handled_error, HandledError)
        assert handled_error.original_error is error
        assert handled_error.contextual_error.context == context
    
    def test_global_create_contextual_exception(self):
        """Test global create_contextual_exception function"""
        message = "Global contextual exception"
        category = ErrorCategory.LOGIC
        
        exception = create_contextual_exception(message, category)
        
        assert isinstance(exception, Exception)
        assert str(exception) == message
        assert exception.contextual_error.category == category


class TestErrorHandlingDecorator:
    """Test suite for error handling decorator"""
    
    def test_handle_errors_decorator(self):
        """Test handle_errors decorator"""
        @handle_errors(category=ErrorCategory.LOGIC, severity=ErrorSeverity.HIGH)
        def test_function():
            raise ValueError("Decorated function error")
        
        with pytest.raises(ValueError) as exc_info:
            test_function()
        
        assert "Decorated function error" in str(exc_info.value)
    
    def test_handle_errors_decorator_with_context(self):
        """Test handle_errors decorator with context extraction"""
        def extract_context(*args, **kwargs):
            return {"args": args, "kwargs": kwargs}
        
        @handle_errors(
            category=ErrorCategory.VALIDATION,
            context_extractor=extract_context
        )
        def test_function_with_args(arg1, arg2, kwarg1=None):
            raise RuntimeError("Function with context error")
        
        with pytest.raises(RuntimeError) as exc_info:
            test_function_with_args("test1", "test2", kwarg1="test3")
        
        assert "Function with context error" in str(exc_info.value)
    
    def test_handle_errors_decorator_success(self):
        """Test handle_errors decorator with successful function"""
        @handle_errors(category=ErrorCategory.LOGIC)
        def successful_function(value):
            return value * 2
        
        result = successful_function(5)
        assert result == 10


class TestRecoveryActions:
    """Test suite for recovery actions"""
    
    def test_recovery_action_creation(self):
        """Test recovery action creation"""
        action = RecoveryAction(
            action_type="test_action",
            description="Test recovery action",
            automated=True
        )
        
        assert action.action_type == "test_action"
        assert action.description == "Test recovery action"
        assert action.automated is True
    
    def test_recovery_actions_registry(self):
        """Test recovery actions registry"""
        handler = StandardizedErrorHandler()
        
        # Check that recovery actions are registered for different categories
        assert ErrorCategory.CONFIGURATION in handler._recovery_actions
        assert ErrorCategory.AUTHENTICATION in handler._recovery_actions
        assert ErrorCategory.NETWORK in handler._recovery_actions
        
        # Check that actions have descriptions
        config_actions = handler._recovery_actions[ErrorCategory.CONFIGURATION]
        assert len(config_actions) > 0
        assert all(action.description for action in config_actions)


class TestEscalationResult:
    """Test suite for escalation results"""
    
    def test_escalation_result_creation(self):
        """Test escalation result creation"""
        result = EscalationResult(
            escalated=True,
            escalation_level="critical",
            notification_sent=True
        )
        
        assert result.escalated is True
        assert result.escalation_level == "critical"
        assert result.notification_sent is True


if __name__ == '__main__':
    pytest.main([__file__])