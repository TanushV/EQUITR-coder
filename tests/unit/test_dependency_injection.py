"""
Unit tests for Dependency Injection Container

Tests the dependency injection system including:
- Service registration and resolution
- Different service lifetimes
- Dependency resolution
- Circular dependency detection
- Interface-based injection
- Scoped services
"""

import pytest
from abc import ABC, abstractmethod
from unittest.mock import MagicMock

from equitrcoder.core.dependency_injection import (
    DependencyInjectionContainer,
    ServiceLifetime,
    ServiceDescriptor,
    DependencyScope,
    DependencyResolutionError,
    CircularDependencyError,
    ServiceNotRegisteredError,
    injectable,
    inject,
    get_container,
    configure_container,
    reset_container,
    register_singleton,
    register_transient,
    register_instance,
    resolve
)


# Test interfaces and classes
class IRepository(ABC):
    @abstractmethod
    def get_data(self) -> str:
        pass


class IService(ABC):
    @abstractmethod
    def process(self) -> str:
        pass


class Repository(IRepository):
    def get_data(self) -> str:
        return "data from repository"


class Service(IService):
    def __init__(self, repository: IRepository):
        self.repository = repository
    
    def process(self) -> str:
        return f"processed: {self.repository.get_data()}"


class ComplexService:
    def __init__(self, service: IService, repository: IRepository):
        self.service = service
        self.repository = repository
    
    def execute(self) -> str:
        return f"complex: {self.service.process()}"


class CircularA:
    def __init__(self, b):  # Remove forward reference for now
        self.b = b


class CircularB:
    def __init__(self, a: CircularA):
        self.a = a


@injectable(ServiceLifetime.SINGLETON)
class SingletonService:
    def __init__(self):
        self.id = id(self)


class DisposableService:
    def __init__(self):
        self.disposed = False
    
    def dispose(self):
        self.disposed = True


class TestServiceDescriptor:
    """Test suite for ServiceDescriptor"""
    
    def test_descriptor_creation(self):
        """Test ServiceDescriptor creation"""
        descriptor = ServiceDescriptor(
            service_type=IRepository,
            implementation_type=Repository,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert descriptor.service_type == IRepository
        assert descriptor.implementation_type == Repository
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.dependencies == []
    
    def test_descriptor_with_dependencies(self):
        """Test ServiceDescriptor with dependencies"""
        dependencies = [IRepository, IService]
        descriptor = ServiceDescriptor(
            service_type=ComplexService,
            implementation_type=ComplexService,
            dependencies=dependencies
        )
        
        assert descriptor.dependencies == dependencies


class TestDependencyInjectionContainer:
    """Test suite for DependencyInjectionContainer"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.container = DependencyInjectionContainer()
    
    def test_container_initialization(self):
        """Test container initialization"""
        assert isinstance(self.container._services, dict)
        assert isinstance(self.container._singletons, dict)
        assert len(self.container._services) == 1  # Container registers itself
        assert self.container.is_registered(DependencyInjectionContainer)
    
    def test_register_singleton(self):
        """Test singleton service registration"""
        self.container.register_singleton(IRepository, Repository)
        
        assert self.container.is_registered(IRepository)
        descriptor = self.container._services[IRepository]
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.implementation_type == Repository
    
    def test_register_transient(self):
        """Test transient service registration"""
        self.container.register_transient(IRepository, Repository)
        
        assert self.container.is_registered(IRepository)
        descriptor = self.container._services[IRepository]
        assert descriptor.lifetime == ServiceLifetime.TRANSIENT
        assert descriptor.implementation_type == Repository
    
    def test_register_scoped(self):
        """Test scoped service registration"""
        self.container.register_scoped(IRepository, Repository)
        
        assert self.container.is_registered(IRepository)
        descriptor = self.container._services[IRepository]
        assert descriptor.lifetime == ServiceLifetime.SCOPED
        assert descriptor.implementation_type == Repository
    
    def test_register_instance(self):
        """Test instance registration"""
        repo_instance = Repository()
        self.container.register_instance(IRepository, repo_instance)
        
        assert self.container.is_registered(IRepository)
        resolved = self.container.resolve(IRepository)
        assert resolved is repo_instance
    
    def test_register_factory(self):
        """Test factory registration"""
        def repo_factory():
            return Repository()
        
        self.container.register_factory(IRepository, repo_factory, ServiceLifetime.TRANSIENT)
        
        assert self.container.is_registered(IRepository)
        resolved = self.container.resolve(IRepository)
        assert isinstance(resolved, Repository)
    
    def test_resolve_simple_service(self):
        """Test resolving a simple service"""
        self.container.register_transient(IRepository, Repository)
        
        resolved = self.container.resolve(IRepository)
        assert isinstance(resolved, Repository)
        assert resolved.get_data() == "data from repository"
    
    def test_resolve_with_dependencies(self):
        """Test resolving service with dependencies"""
        self.container.register_transient(IRepository, Repository)
        self.container.register_transient(IService, Service)
        
        resolved = self.container.resolve(IService)
        assert isinstance(resolved, Service)
        assert isinstance(resolved.repository, Repository)
        assert resolved.process() == "processed: data from repository"
    
    def test_resolve_complex_dependencies(self):
        """Test resolving service with multiple dependencies"""
        self.container.register_transient(IRepository, Repository)
        self.container.register_transient(IService, Service)
        self.container.register_transient(ComplexService)
        
        resolved = self.container.resolve(ComplexService)
        assert isinstance(resolved, ComplexService)
        assert isinstance(resolved.service, Service)
        assert isinstance(resolved.repository, Repository)
        assert resolved.execute() == "complex: processed: data from repository"
    
    def test_singleton_lifetime(self):
        """Test singleton lifetime behavior"""
        self.container.register_singleton(IRepository, Repository)
        
        instance1 = self.container.resolve(IRepository)
        instance2 = self.container.resolve(IRepository)
        
        assert instance1 is instance2
    
    def test_transient_lifetime(self):
        """Test transient lifetime behavior"""
        self.container.register_transient(IRepository, Repository)
        
        instance1 = self.container.resolve(IRepository)
        instance2 = self.container.resolve(IRepository)
        
        assert instance1 is not instance2
        assert isinstance(instance1, Repository)
        assert isinstance(instance2, Repository)
    
    def test_scoped_lifetime(self):
        """Test scoped lifetime behavior"""
        self.container.register_scoped(IRepository, Repository)
        
        # Within same scope, should return same instance
        instance1 = self.container.resolve(IRepository)
        instance2 = self.container.resolve(IRepository)
        assert instance1 is instance2
        
        # After clearing scoped instances, should create new instance
        self.container.clear_scoped_instances()
        instance3 = self.container.resolve(IRepository)
        assert instance1 is not instance3
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        # Manually set up circular dependencies since type annotations are tricky
        descriptor_a = ServiceDescriptor(
            service_type=CircularA,
            implementation_type=CircularA,
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=[CircularB]
        )
        descriptor_b = ServiceDescriptor(
            service_type=CircularB,
            implementation_type=CircularB,
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=[CircularA]
        )
        
        self.container._services[CircularA] = descriptor_a
        self.container._services[CircularB] = descriptor_b
        
        with pytest.raises(CircularDependencyError) as exc_info:
            self.container.resolve(CircularA)
        
        assert "Circular dependency detected" in str(exc_info.value)
        assert "CircularA" in str(exc_info.value)
        assert "CircularB" in str(exc_info.value)
    
    def test_service_not_registered_error(self):
        """Test error when service is not registered"""
        with pytest.raises(ServiceNotRegisteredError) as exc_info:
            self.container.resolve(IRepository)
        
        assert "IRepository is not registered" in str(exc_info.value)
    
    def test_try_resolve(self):
        """Test try_resolve method"""
        # Unregistered service should return None
        result = self.container.try_resolve(IRepository)
        assert result is None
        
        # Registered service should return instance
        self.container.register_transient(IRepository, Repository)
        result = self.container.try_resolve(IRepository)
        assert isinstance(result, Repository)
    
    def test_get_registered_services(self):
        """Test getting list of registered services"""
        initial_count = len(self.container.get_registered_services())
        
        self.container.register_transient(IRepository, Repository)
        self.container.register_singleton(IService, Service)
        
        services = self.container.get_registered_services()
        assert len(services) == initial_count + 2
        assert IRepository in services
        assert IService in services


class TestDependencyScope:
    """Test suite for DependencyScope"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.container = DependencyInjectionContainer()
        self.container.register_scoped(DisposableService)
    
    def test_scope_creation(self):
        """Test creating a dependency scope"""
        scope = self.container.create_scope()
        assert isinstance(scope, DependencyScope)
    
    def test_scoped_resolution(self):
        """Test resolving services within a scope"""
        with self.container.create_scope() as scope:
            instance1 = scope.resolve(DisposableService)
            instance2 = scope.resolve(DisposableService)
            
            # Should be same instance within scope
            assert instance1 is instance2
    
    def test_scope_isolation(self):
        """Test that different scopes have different instances"""
        with self.container.create_scope() as scope1:
            instance1 = scope1.resolve(DisposableService)
        
        with self.container.create_scope() as scope2:
            instance2 = scope2.resolve(DisposableService)
        
        assert instance1 is not instance2
    
    def test_scope_disposal(self):
        """Test that scoped instances are disposed"""
        instance = None
        
        with self.container.create_scope() as scope:
            instance = scope.resolve(DisposableService)
            assert not instance.disposed
        
        # After scope exit, instance should be disposed
        assert instance.disposed


class TestDecorators:
    """Test suite for dependency injection decorators"""
    
    def test_injectable_decorator(self):
        """Test injectable decorator"""
        @injectable(ServiceLifetime.SINGLETON)
        class TestService:
            pass
        
        assert hasattr(TestService, '_di_lifetime')
        assert TestService._di_lifetime == ServiceLifetime.SINGLETON
    
    def test_inject_decorator(self):
        """Test inject decorator"""
        container = DependencyInjectionContainer()
        container.register_instance(str, "injected_value")
        
        @inject(container)
        def test_function(value: str):
            return f"received: {value}"
        
        result = test_function()
        assert result == "received: injected_value"
    
    def test_inject_decorator_with_existing_args(self):
        """Test inject decorator with existing arguments"""
        container = DependencyInjectionContainer()
        container.register_instance(str, "injected_value")
        
        @inject(container)
        def test_function(value: str, other: int = 42):
            return f"received: {value}, other: {other}"
        
        # Explicit argument should override injection
        result = test_function(value="explicit_value")
        assert result == "received: explicit_value, other: 42"


class TestGlobalContainer:
    """Test suite for global container functions"""
    
    def setup_method(self):
        """Setup for each test method"""
        reset_container()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        reset_container()
    
    def test_get_container(self):
        """Test getting global container"""
        container1 = get_container()
        container2 = get_container()
        
        # Should return same instance (singleton)
        assert container1 is container2
        assert isinstance(container1, DependencyInjectionContainer)
    
    def test_configure_container(self):
        """Test configuring global container"""
        custom_container = DependencyInjectionContainer()
        custom_container.register_instance(str, "custom")
        
        configure_container(custom_container)
        
        container = get_container()
        assert container is custom_container
        assert container.resolve(str) == "custom"
    
    def test_reset_container(self):
        """Test resetting global container"""
        container1 = get_container()
        reset_container()
        container2 = get_container()
        
        assert container1 is not container2
    
    def test_global_convenience_functions(self):
        """Test global convenience functions"""
        # Test registration functions
        register_singleton(IRepository, Repository)
        register_transient(IService, Service)
        register_instance(str, "test_value")
        
        # Test resolution
        repo = resolve(IRepository)
        service = resolve(IService)
        value = resolve(str)
        
        assert isinstance(repo, Repository)
        assert isinstance(service, Service)
        assert value == "test_value"
        
        # Test singleton behavior
        repo2 = resolve(IRepository)
        assert repo is repo2
        
        # Test transient behavior
        service2 = resolve(IService)
        assert service is not service2


class TestComplexScenarios:
    """Test suite for complex dependency injection scenarios"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.container = DependencyInjectionContainer()
    
    def test_mixed_lifetimes(self):
        """Test services with mixed lifetimes"""
        self.container.register_singleton(IRepository, Repository)
        self.container.register_transient(IService, Service)
        
        # Resolve multiple times
        service1 = self.container.resolve(IService)
        service2 = self.container.resolve(IService)
        
        # Services should be different (transient)
        assert service1 is not service2
        
        # But their repositories should be the same (singleton)
        assert service1.repository is service2.repository
    
    def test_factory_with_dependencies(self):
        """Test factory that creates services with dependencies"""
        self.container.register_singleton(IRepository, Repository)
        
        def service_factory():
            repo = self.container.resolve(IRepository)
            return Service(repo)
        
        self.container.register_factory(IService, service_factory, ServiceLifetime.TRANSIENT)
        
        service = self.container.resolve(IService)
        assert isinstance(service, Service)
        assert isinstance(service.repository, Repository)
    
    def test_conditional_registration(self):
        """Test conditional service registration"""
        # Register different implementations based on conditions
        if True:  # Simulate condition
            self.container.register_singleton(IRepository, Repository)
        else:
            # Would register different implementation
            pass
        
        resolved = self.container.resolve(IRepository)
        assert isinstance(resolved, Repository)
    
    def test_service_replacement(self):
        """Test replacing a registered service"""
        # Register initial service
        self.container.register_singleton(IRepository, Repository)
        instance1 = self.container.resolve(IRepository)
        
        # Replace with new registration
        new_repo = Repository()
        self.container.register_instance(IRepository, new_repo)
        instance2 = self.container.resolve(IRepository)
        
        assert instance1 is not instance2
        assert instance2 is new_repo


if __name__ == '__main__':
    pytest.main([__file__])