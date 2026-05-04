# Proposal: Dependency Injection Refactor for Circular Import Elimination

## Intent
Eliminate circular dependencies and scattered lazy imports across the `fu7ur3pr00f` codebase by formalizing the `Container` as a layered Dependency Injection (DI) provider and implementing deferred initialization in core services.

## Scope
The refactor targets the core orchestration and service layers:
- **`src/fu7ur3pr00f/container.py`**: Transition from a simple lazy-loading bag to a structured, layered container.
- **`src/fu7ur3pr00f/agents/specialists/routing.py`**: Decouple `RoutingService` from specialist implementations to break the specialist $\leftrightarrow$ routing cycle.
- **`src/fu7ur3pr00f/agents/specialists/orchestrator.py`**: Remove eager container property access in `__init__`.
- **`src/fu7ur3pr00f/agents/specialists/blackboard_factory.py`**: Implement deferred specialist registration.

## Approach

### 1. Layered Container Architecture
We will organize the `Container` properties into a strict hierarchy to prevent backward dependencies:
- **Layer 1: Config** (`Settings`, `SecurityUtils`) $\rightarrow$ No dependencies.
- **Layer 2: Memory/Data** (`UserProfile`, `KnowledgeStore`, `Checkpointer`) $\rightarrow$ Depends on Layer 1.
- **Layer 3: Services** (`KnowledgeService`, `GathererService`, `ModelSelectionManager`) $\rightarrow$ Depends on Layer 1 & 2.
- **Layer 4: Agents** (`RoutingService`, `BlackboardFactory`, `OrchestratorAgent`) $\rightarrow$ Depends on Layer 1, 2 & 3.
- **Layer 5: Graph** (`ConversationGraph`) $\rightarrow$ Depends on all below.

### 2. Deferred Routing Initialization
Currently, `RoutingService.__init__` instantiates all specialists, which requires importing them, which in turn might require the container/routing service.
**Change**: Move instantiation to a private `_ensure_specialists()` method called only when `get_specialist()` or `route()` is invoked.

### 3. Property-Based Lazy Access
Replace `self.routing = container.routing_service` in `__init__` methods with:
```python
@property
def routing(self) -> RoutingService:
    return container.routing_service
```
This ensures that services are only resolved when actually needed, avoiding initialization-time circularities.

## Trade-offs
- **Lightweight Container vs. DI Framework**: We chose to extend the existing `container.py` rather than introducing a framework like `dependency-injector`. While a framework provides better type-safety and injection patterns, it would introduce significant boilerplate and a steep learning curve for a project of this size. The lightweight approach maintains simplicity while solving the circularity problem.
- **Runtime Overhead**: Property-based lazy loading adds a negligible overhead to the first access of a service but significantly simplifies the dependency graph.

## Success Criteria
- Zero `ImportError` or `AttributeError` related to circular dependencies during startup.
- Removal of all module-level lazy imports (imports inside functions) that were used solely to break circularities.
- Passing all existing tests in `tests/`.
