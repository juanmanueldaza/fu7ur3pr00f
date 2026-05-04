# Specification: Dependency Injection Refactor

## Overview
This specification details the transition of the `fu7ur3pr00f` dependency management from scattered lazy imports to a structured, layered Dependency Injection (DI) container.

## Requirements

### 1. Layered Container Structure
The `Container` class in `src/fu7ur3pr00f/container.py` must implement properties in the following order of dependency:
1. **Config Layer**: `settings`, `security`.
2. **Memory Layer**: `profile`, `knowledge_store`, `checkpointer`, `embedding_function`.
3. **Services Layer**: `knowledge_service`, `gather_service`, `model_manager`.
4. **Agents Layer**: `routing_service`, `blackboard_factory`, `orchestrator`.
5. **Graph Layer**: `conversation_graph`.

Each property must implement a lazy-loading pattern:
```python
@property
def service_name(self) -> ServiceType:
    if self._service_name is None:
        from .path import ServiceType
        self._service_name = ServiceType(...)
    return self._service_name
```

### 2. Deferred Specialist Initialization
The `RoutingService` in `src/fu7ur3pr00f/agents/specialists/routing.py` must:
- Remove specialist imports from the module level.
- Remove specialist instantiation from `__init__`.
- Implement `_ensure_specialists()` which imports and instantiates `CoachAgent`, `CodeAgent`, `FounderAgent`, `JobsAgent`, and `LearningAgent`.
- Call `_ensure_specialists()` inside any method that accesses `self._specialists`.

### 3. Lazy Service Access in Agents
`OrchestratorAgent` and `BlackboardFactory` must:
- Remove direct assignments of container services in `__init__`.
- Use `@property` decorators to access required services from the `container` singleton.

## Scenarios

### Scenario 1: System Startup
**Given** the application is starting up.
**When** the first agent is requested.
**Then** the `Container` should lazily resolve dependencies in the correct order (Config $\rightarrow$ Memory $\rightarrow$ Service $\rightarrow$ Agent) without triggering a circular import error.

### Scenario 2: Routing a Query
**Given** a user query is passed to `RoutingService.route()`.
**When** the method is called.
**Then** `_ensure_specialists()` should be triggered, specialists should be instantiated, and the correct specialist should be returned.

### Scenario 3: Service Reset
**Given** a `factory_reset()` is called.
**When** `container.reset_all()` is invoked.
**Then** all layered cached services should be set to `None`, ensuring the next access re-initializes them with fresh settings.

## Validation
- **Static Analysis**: `pyright` or `mypy` should show no type errors in `container.py` or `routing.py`.
- **Runtime**: Run `python -c "from fu7ur3pr00f.container import container; print(container.orchestrator)"` and ensure it completes without `ImportError`.
- **Tests**: All tests in `tests/` must pass.
