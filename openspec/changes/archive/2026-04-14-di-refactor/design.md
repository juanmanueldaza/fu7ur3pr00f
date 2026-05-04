# Design: Dependency Injection Refactor

## Architecture Changes

### 1. `src/fu7ur3pr00f/container.py`
We will refactor the `Container` class to explicitly separate its state and lazy-loading properties.

**State Variables**:
- `_settings`, `_security` (Config)
- `_profile`, `_knowledge_store`, `_checkpointer`, `_embedding_function` (Memory)
- `_knowledge_service`, `_gather_service`, `_model_manager` (Services)
- `_routing_service`, `_blackboard_factory`, `_orchestrator` (Agents)
- `_conversation_graph` (Graph)

**Logic**:
- Each property follows the pattern: `if self._var is None: from ... import ...; self._var = ...`.
- `reset_services()` will clear Layer 3 and 4.
- `reset_all()` will clear all layers.

### 2. `src/fu7ur3pr00f/agents/specialists/routing.py`
**Change**:
- Remove: `from fu7ur3pr00f.agents.specialists import CoachAgent, ...` from top of file.
- Modify `__init__`: Initialize `self._specialists = {}` and `self._initialized = False`.
- Add `_ensure_specialists()`:
  ```python
  def _ensure_specialists(self) -> None:
      if self._initialized: return
      from fu7ur3pr00f.agents.specialists import CoachAgent, CodeAgent, ...
      self._specialists = {
          "coach": CoachAgent(),
          ...
      }
      self._initialized = True
  ```
- Update `route()` and `get_specialist()` to call `self._ensure_specialists()` first.

### 3. `src/fu7ur3pr00f/agents/specialists/orchestrator.py`
**Change**:
- Remove `self._routing = container.routing_service` from `__init__`.
- Add property:
  ```python
  @property
  def routing(self) -> RoutingService:
      return container.routing_service
  ```
- Update all references from `self._routing` to `self.routing`.

### 4. `src/fu7ur3pr00f/agents/specialists/blackboard_factory.py`
**Change**:
- Remove eager container access in `__init__`.
- Implement lazy property access for `routing_service` and other dependencies.

## Implementation Plan
1. **Container First**: Update `container.py` to the new layered structure.
2. **Routing Decoupling**: Refactor `RoutingService` to use deferred initialization.
3. **Agent Cleanup**: Update `OrchestratorAgent` and `BlackboardFactory`.
4. **Validation**: Verify with `pyright` and startup tests.
