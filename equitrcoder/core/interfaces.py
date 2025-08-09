"""
Standardized Interfaces for EQUITR Coder

This module defines common interfaces and base classes to ensure
consistent patterns across similar functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import inspect

T = TypeVar('T')


class Status(Enum):
    """Standard status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Result(Generic[T]):
    """Standard result wrapper for operations"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IGenerator(ABC, Generic[T]):
    """Interface for content generators"""
    
    @abstractmethod
    async def generate(self, *args, **kwargs) -> T:
        """Generate content based on input parameters"""
        pass
    
    @abstractmethod
    async def generate_interactive(self, *args, **kwargs) -> Any:
        """Generate content through interactive process (return type may vary by implementation)"""
        pass


class IValidator(ABC, Generic[T]):
    """Interface for validators"""
    
    @abstractmethod
    def validate(self, item: T) -> Result[bool]:
        """Validate an item and return result with details"""
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> List[str]:
        """Get list of validation rules"""
        pass


class IProcessor(ABC, Generic[T]):
    """Interface for processors that transform data"""
    
    @abstractmethod
    async def process(self, input_data: T) -> Result[T]:
        """Process input data and return result"""
        pass
    
    @abstractmethod
    def can_process(self, input_data: T) -> bool:
        """Check if this processor can handle the input data"""
        pass


class IRepository(ABC, Generic[T]):
    """Interface for data repositories"""
    
    @abstractmethod
    async def create(self, item: T) -> Result[T]:
        """Create a new item"""
        pass
    
    @abstractmethod
    async def get(self, id: str) -> Result[Optional[T]]:
        """Get an item by ID"""
        pass
    
    @abstractmethod
    async def update(self, id: str, item: T) -> Result[T]:
        """Update an existing item"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> Result[bool]:
        """Delete an item by ID"""
        pass
    
    @abstractmethod
    async def list(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[T]]:
        """List items with optional filters"""
        pass


class ICache(ABC, Generic[T]):
    """Interface for caching systems"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get item from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set item in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete item from cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all items from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass


class IMonitor(ABC):
    """Interface for monitoring systems"""
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """Start monitoring"""
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop monitoring"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        pass
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        pass


class IConfigurable(ABC):
    """Interface for configurable components"""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> Result[bool]:
        """Configure the component with given settings"""
        pass
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration"""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> Result[bool]:
        """Validate configuration before applying"""
        pass


class IDisposable(ABC):
    """Interface for components that need cleanup"""
    
    @abstractmethod
    def dispose(self) -> None:
        """Clean up resources"""
        pass


class IHealthCheck(ABC):
    """Interface for health checking"""
    
    @abstractmethod
    async def check_health(self) -> Result[Dict[str, Any]]:
        """Check component health and return status"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> Status:
        """Get current health status"""
        pass


class IEventEmitter(ABC):
    """Interface for event emission"""
    
    @abstractmethod
    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event with optional data"""
        pass
    
    @abstractmethod
    def on(self, event: str, handler: Callable[..., Any]) -> None:
        """Register event handler"""
        pass
    
    @abstractmethod
    def off(self, event: str, handler: Callable[..., Any]) -> None:
        """Unregister event handler"""
        pass


class ISerializer(ABC, Generic[T]):
    """Interface for serialization"""
    
    @abstractmethod
    def serialize(self, obj: T) -> str:
        """Serialize object to string"""
        pass
    
    @abstractmethod
    def deserialize(self, data: str) -> T:
        """Deserialize string to object"""
        pass
    
    @abstractmethod
    def get_format(self) -> str:
        """Get serialization format (json, yaml, etc.)"""
        pass


class IFactory(ABC, Generic[T]):
    """Interface for factory patterns"""
    
    @abstractmethod
    def create(self, type_name: str, **kwargs) -> T:
        """Create instance of specified type"""
        pass
    
    @abstractmethod
    def register(self, type_name: str, creator: Callable[..., T]) -> None:
        """Register a creator function for a type"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get list of supported types"""
        pass


class IPlugin(ABC):
    """Interface for plugin systems"""
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> Result[bool]:
        """Initialize the plugin with context"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get plugin version"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of plugin dependencies"""
        pass


# Base classes that implement common patterns

class BaseRepository(IRepository[T]):
    """Base repository implementation with common functionality"""
    
    def __init__(self):
        self._items: Dict[str, T] = {}
    
    async def create(self, item: T) -> Result[T]:
        """Base create implementation"""
        try:
            item_id = self._generate_id(item)
            self._items[item_id] = item
            return Result(success=True, data=item)
        except Exception as e:
            return Result(success=False, error=str(e))
    
    async def get(self, id: str) -> Result[Optional[T]]:
        """Base get implementation"""
        try:
            item = self._items.get(id)
            return Result(success=True, data=item)
        except Exception as e:
            return Result(success=False, error=str(e))
    
    async def update(self, id: str, item: T) -> Result[T]:
        """Base update implementation"""
        try:
            if id not in self._items:
                return Result(success=False, error=f"Item {id} not found")
            self._items[id] = item
            return Result(success=True, data=item)
        except Exception as e:
            return Result(success=False, error=str(e))
    
    async def delete(self, id: str) -> Result[bool]:
        """Base delete implementation"""
        try:
            if id in self._items:
                del self._items[id]
                return Result(success=True, data=True)
            return Result(success=False, error=f"Item {id} not found")
        except Exception as e:
            return Result(success=False, error=str(e))
    
    async def list(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[T]]:
        """Base list implementation"""
        try:
            items = list(self._items.values())
            if filters:
                items = self._apply_filters(items, filters)
            return Result(success=True, data=items)
        except Exception as e:
            return Result(success=False, error=str(e))
    
    def _generate_id(self, item: T) -> str:
        """Generate ID for item - override in subclasses"""
        import uuid
        return str(uuid.uuid4())
    
    def _apply_filters(self, items: List[T], filters: Dict[str, Any]) -> List[T]:
        """Apply filters to items - override in subclasses"""
        return items


class BaseValidator(IValidator[T]):
    """Base validator with common validation patterns"""
    
    def __init__(self):
        self.rules: List[Callable[[Any], bool]] = []
    
    def validate(self, item: T) -> Result[bool]:
        """Validate item against all rules"""
        errors: List[str] = []
        
        for rule in self.rules:
            try:
                if not rule(item):
                    rule_name = getattr(rule, "__name__", repr(rule))
                    errors.append(f"Validation rule failed: {rule_name}")
            except Exception as e:
                rule_name = getattr(rule, "__name__", repr(rule))
                errors.append(f"Validation error in {rule_name}: {str(e)}")
        
        if errors:
            return Result(success=False, error="; ".join(errors))
        
        return Result(success=True, data=True)
    
    def get_validation_rules(self) -> List[str]:
        """Get list of validation rule names"""
        return [getattr(rule, "__name__", repr(rule)) for rule in self.rules]
    
    def add_rule(self, rule: Callable[[Any], bool]) -> None:
        """Add a validation rule"""
        self.rules.append(rule)


class BaseProcessor(IProcessor[T]):
    """Base processor with common processing patterns"""
    
    def __init__(self):
        self.processors: List[Callable[[Any], Any]] = []
    
    async def process(self, input_data: T) -> Result[T]:
        """Process data through all processors"""
        try:
            result: Any = input_data
            for processor in self.processors:
                result = await self._apply_processor(processor, result)
            return Result(success=True, data=result)
        except Exception as e:
            return Result(success=False, error=str(e))
    
    def can_process(self, input_data: T) -> bool:
        """Check if this processor can handle the input"""
        return True  # Override in subclasses
    
    def add_processor(self, processor: Callable[[Any], Any]) -> None:
        """Add a processing step"""
        self.processors.append(processor)
    
    async def _apply_processor(self, processor: Callable[[Any], Any], data: T) -> T:
        """Apply a single processor"""
        result = processor(data)
        if inspect.isawaitable(result):
            from typing import cast
            return cast(T, await result)
        from typing import cast
        return cast(T, result)


class BaseConfigurable(IConfigurable):
    """Base configurable component"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._default_config: Dict[str, Any] = {}
    
    def configure(self, config: Dict[str, Any]) -> Result[bool]:
        """Configure with validation"""
        validation_result = self.validate_configuration(config)
        if not validation_result.success:
            return validation_result
        
        self._config.update(config)
        return Result(success=True, data=True)
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {**self._default_config, **self._config}
    
    def validate_configuration(self, config: Dict[str, Any]) -> Result[bool]:
        """Basic configuration validation"""
        # Override in subclasses for specific validation
        return Result(success=True, data=True)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value"""
        return self.get_configuration().get(key, default)