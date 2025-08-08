"""
Dependency Injection Container for EQUITR Coder

This module provides a dependency injection system for loose coupling
between components, implementing interface-based component interaction
and dependency resolution with lifecycle management.

Features:
- Service registration and resolution
- Interface-based dependency injection
- Singleton and transient lifetimes
- Circular dependency detection
- Automatic dependency resolution
- Component lifecycle management
"""

import threading
import inspect
from typing import Any, Dict, Type, TypeVar, Callable, Optional, List, Set
# Removed unused ABC imports
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Describes a registered service"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DependencyResolutionError(Exception):
    """Raised when dependency resolution fails"""
    pass


class CircularDependencyError(DependencyResolutionError):
    """Raised when circular dependencies are detected"""
    pass


class ServiceNotRegisteredError(DependencyResolutionError):
    """Raised when a requested service is not registered"""
    pass


class DependencyInjectionContainer:
    """
    Dependency injection container for managing service registration and resolution
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack: Set[Type] = set()
        
        # Register the container itself
        self.register_instance(DependencyInjectionContainer, self)
    
    def register_singleton(self, service_type: Type[T], implementation_type: Type[T] = None) -> 'DependencyInjectionContainer':
        """
        Register a service as singleton (single instance for the lifetime of the container)
        
        Args:
            service_type: The service interface or base type
            implementation_type: The concrete implementation type
            
        Returns:
            Self for method chaining
        """
        return self._register_service(service_type, implementation_type, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation_type: Type[T] = None) -> 'DependencyInjectionContainer':
        """
        Register a service as transient (new instance every time)
        
        Args:
            service_type: The service interface or base type
            implementation_type: The concrete implementation type
            
        Returns:
            Self for method chaining
        """
        return self._register_service(service_type, implementation_type, ServiceLifetime.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], implementation_type: Type[T] = None) -> 'DependencyInjectionContainer':
        """
        Register a service as scoped (single instance per scope)
        
        Args:
            service_type: The service interface or base type
            implementation_type: The concrete implementation type
            
        Returns:
            Self for method chaining
        """
        return self._register_service(service_type, implementation_type, ServiceLifetime.SCOPED)
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DependencyInjectionContainer':
        """
        Register a specific instance for a service type
        
        Args:
            service_type: The service type
            instance: The instance to register
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON
            )
            self._services[service_type] = descriptor
            self._singletons[service_type] = instance
            
            logger.debug(f"Registered instance for {service_type.__name__}")
            return self
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T], 
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DependencyInjectionContainer':
        """
        Register a factory function for creating service instances
        
        Args:
            service_type: The service type
            factory: Factory function that creates instances
            lifetime: Service lifetime
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifetime=lifetime
            )
            self._services[service_type] = descriptor
            
            logger.debug(f"Registered factory for {service_type.__name__} with {lifetime.value} lifetime")
            return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotRegisteredError: If service is not registered
            CircularDependencyError: If circular dependency is detected
        """
        with self._lock:
            return self._resolve_service(service_type)
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service instance, returning None if not found
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Service instance or None if not found
        """
        try:
            return self.resolve(service_type)
        except ServiceNotRegisteredError:
            return None
    
    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered
        
        Args:
            service_type: The service type to check
            
        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            return service_type in self._services
    
    def get_registered_services(self) -> List[Type]:
        """
        Get list of all registered service types
        
        Returns:
            List of registered service types
        """
        with self._lock:
            return list(self._services.keys())
    
    def create_scope(self) -> 'DependencyScope':
        """
        Create a new dependency scope for scoped services
        
        Returns:
            New dependency scope
        """
        return DependencyScope(self)
    
    def clear_scoped_instances(self) -> None:
        """Clear all scoped instances"""
        with self._lock:
            self._scoped_instances.clear()
            logger.debug("Cleared scoped instances")
    
    def _register_service(self, service_type: Type[T], implementation_type: Type[T], 
                         lifetime: ServiceLifetime) -> 'DependencyInjectionContainer':
        """Internal method to register a service"""
        if implementation_type is None:
            implementation_type = service_type
        
        with self._lock:
            # Analyze dependencies
            dependencies = self._analyze_dependencies(implementation_type)
            
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=lifetime,
                dependencies=dependencies
            )
            self._services[service_type] = descriptor
            
            logger.debug(f"Registered {service_type.__name__} -> {implementation_type.__name__} "
                        f"with {lifetime.value} lifetime")
            return self
    
    def _resolve_service(self, service_type: Type[T]) -> T:
        """Internal method to resolve a service"""
        # Check for circular dependency
        if service_type in self._resolution_stack:
            cycle = " -> ".join([t.__name__ for t in self._resolution_stack]) + f" -> {service_type.__name__}"
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")
        
        # Check if service is registered
        if service_type not in self._services:
            raise ServiceNotRegisteredError(f"Service {service_type.__name__} is not registered")
        
        descriptor = self._services[service_type]
        
        # Return existing instance if available
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Check singleton cache
        if descriptor.lifetime == ServiceLifetime.SINGLETON and service_type in self._singletons:
            return self._singletons[service_type]
        
        # Check scoped cache
        if descriptor.lifetime == ServiceLifetime.SCOPED and service_type in self._scoped_instances:
            return self._scoped_instances[service_type]
        
        # Create new instance
        self._resolution_stack.add(service_type)
        try:
            instance = self._create_instance(descriptor)
            
            # Cache instance based on lifetime
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[service_type] = instance
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                self._scoped_instances[service_type] = instance
            
            return instance
        finally:
            self._resolution_stack.discard(service_type)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance from a service descriptor"""
        if descriptor.factory:
            return descriptor.factory()
        
        if descriptor.implementation_type:
            # Resolve constructor dependencies
            constructor_args = []
            for dep_type in descriptor.dependencies:
                dep_instance = self._resolve_service(dep_type)
                constructor_args.append(dep_instance)
            
            return descriptor.implementation_type(*constructor_args)
        
        raise DependencyResolutionError(f"Cannot create instance for {descriptor.service_type.__name__}")
    
    def _analyze_dependencies(self, implementation_type: Type) -> List[Type]:
        """Analyze constructor dependencies of a type"""
        try:
            signature = inspect.signature(implementation_type.__init__)
            dependencies = []
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    # Handle forward references (strings)
                    if isinstance(param.annotation, str):
                        # Try to resolve the string annotation to a type
                        try:
                            # Get the module where the class is defined
                            module = inspect.getmodule(implementation_type)
                            if module and hasattr(module, param.annotation):
                                dependencies.append(getattr(module, param.annotation))
                            else:
                                logger.warning(f"Cannot resolve forward reference '{param.annotation}' "
                                             f"in {implementation_type.__name__}")
                        except Exception:
                            logger.warning(f"Failed to resolve forward reference '{param.annotation}' "
                                         f"in {implementation_type.__name__}")
                    else:
                        dependencies.append(param.annotation)
                else:
                    logger.warning(f"Parameter {param_name} in {implementation_type.__name__} "
                                 f"has no type annotation")
            
            return dependencies
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies for {implementation_type.__name__}: {e}")
            return []


class DependencyScope:
    """
    Dependency scope for managing scoped service instances
    """
    
    def __init__(self, container: DependencyInjectionContainer):
        self._container = container
        self._scoped_instances: Dict[Type, Any] = {}
        self._original_scoped_instances = container._scoped_instances.copy()
    
    def __enter__(self) -> 'DependencyScope':
        """Enter the scope context"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the scope context and clean up scoped instances"""
        self.dispose()
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service within this scope
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Service instance
        """
        # Use container's resolution but with our scoped instances
        original_scoped = self._container._scoped_instances
        self._container._scoped_instances = self._scoped_instances
        
        try:
            return self._container.resolve(service_type)
        finally:
            # Update our scoped instances with any new ones created
            self._scoped_instances.update(self._container._scoped_instances)
            self._container._scoped_instances = original_scoped
    
    def dispose(self) -> None:
        """Dispose of all scoped instances"""
        for instance in self._scoped_instances.values():
            if hasattr(instance, 'dispose'):
                try:
                    instance.dispose()
                except Exception as e:
                    logger.warning(f"Error disposing scoped instance: {e}")
        
        self._scoped_instances.clear()
        self._container._scoped_instances = self._original_scoped_instances


# Decorators for dependency injection
def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """
    Decorator to mark a class as injectable
    
    Args:
        lifetime: Service lifetime
    """
    def decorator(cls):
        cls._di_lifetime = lifetime
        return cls
    return decorator


def inject(container: DependencyInjectionContainer):
    """
    Decorator to inject dependencies into a function
    
    Args:
        container: Dependency injection container
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Resolve dependencies based on function signature
            signature = inspect.signature(func)
            injected_kwargs = {}
            
            for param_name, param in signature.parameters.items():
                if param.annotation != inspect.Parameter.empty and param_name not in kwargs:
                    try:
                        injected_kwargs[param_name] = container.resolve(param.annotation)
                    except ServiceNotRegisteredError:
                        pass  # Skip unregistered dependencies
            
            return func(*args, **kwargs, **injected_kwargs)
        return wrapper
    return decorator


# Global container instance
_global_container: Optional[DependencyInjectionContainer] = None
_container_lock = threading.Lock()


def get_container() -> DependencyInjectionContainer:
    """Get the global dependency injection container"""
    global _global_container
    
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DependencyInjectionContainer()
    
    return _global_container


def configure_container(container: DependencyInjectionContainer) -> None:
    """Configure the global container"""
    global _global_container
    
    with _container_lock:
        _global_container = container


def reset_container() -> None:
    """Reset the global container"""
    global _global_container
    
    with _container_lock:
        _global_container = None


# Convenience functions
def register_singleton(service_type: Type[T], implementation_type: Type[T] = None) -> DependencyInjectionContainer:
    """Register a singleton service in the global container"""
    return get_container().register_singleton(service_type, implementation_type)


def register_transient(service_type: Type[T], implementation_type: Type[T] = None) -> DependencyInjectionContainer:
    """Register a transient service in the global container"""
    return get_container().register_transient(service_type, implementation_type)


def register_instance(service_type: Type[T], instance: T) -> DependencyInjectionContainer:
    """Register an instance in the global container"""
    return get_container().register_instance(service_type, instance)


def resolve(service_type: Type[T]) -> T:
    """Resolve a service from the global container"""
    return get_container().resolve(service_type)