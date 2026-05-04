# Tasks: Dependency Injection Refactor

## Phase 1: Container Layering
- [x] **T1.1**: Refactor `src/fu7ur3pr00f/container.py` state variables to reflect the 5-layer architecture.
- [x] **T1.2**: Implement lazy-loading properties for all services in `container.py` following the layer hierarchy.
- [x] **T1.3**: Update `reset_services()` and `reset_all()` in `container.py` to clear caches by layer.

## Phase 2: Routing Service Decoupling
- [x] **T2.1**: Remove module-level specialist imports in `src/fu7ur3pr00f/agents/specialists/routing.py`.
- [x] **T2.2**: Implement `_ensure_specialists()` in `RoutingService` for deferred instantiation.
- [x] **T2.3**: Update `RoutingService.route()` and `RoutingService.get_specialist()` to trigger `_ensure_specialists()`.

## Phase 3: Agent Lazy Access
- [x] **T3.1**: Refactor `src/fu7ur3pr00f/agents/specialists/orchestrator.py` to use `@property` for container service access.
- [x] **T3.2**: Refactor `src/fu7ur3pr00f/agents/specialists/blackboard_factory.py` to use `@property` for container service access.

## Phase 4: Verification
- [x] **T4.1**: Run `pyright src/fu7ur3pr00f` to ensure no type errors.
- [x] **T4.2**: Execute a startup probe: `python -c "from fu7ur3pr00f.container import container; print(container.orchestrator)"`.
- [x] **T4.3**: Run full test suite: `pytest tests/ -q`.
