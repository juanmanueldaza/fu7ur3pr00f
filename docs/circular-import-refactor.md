# Circular Import Refactor Plan

## Problem Statement
The codebase uses lazy imports inside functions to break circular dependency chains.
This is a pragmatic workaround but creates maintenance issues:
- Harder to trace actual dependencies
- LSP false positives on unused imports
- Every test must patch at the source module, not the call site
- New developers may not understand why imports are inside functions

## Dependency Graph (Current)

```
config.py ←──── base.py (via get_model, load_prompt)
    ↑               ↑
    │               │
utils/security.py   │
    ↑               │
    │               │
tools/*.py ─────────┘
    ↑
specialists/*.py
```

Circular chain: `tools/market.py` → `gatherers/market.py` → (eventually) `config.py`
And: `base.py` → `llm/model_selection.py` → `config.py`

## Proposed Architecture (Target)

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  CLI/UI   │  │  Agents  │  │   Tools   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                    │
│       ▼              ▼              ▼                    │
│  ┌────────────────────────────────────────┐             │
│  │              Services Layer             │             │
│  │  (GathererService, KnowledgeService)   │             │
│  └────────────────┬───────────────────────┘             │
│                   │                                      │
│                   ▼                                      │
│  ┌────────────────────────────────────────┐             │
│  │           Infrastructure Layer          │             │
│  │  (LLM providers, MCP clients, memory)  │             │
│  └────────────────┬───────────────────────┘             │
│                   │                                      │
│                   ▼                                      │
│  ┌────────────────────────────────────────┐             │
│  │              Config Layer               │             │
│  │  (Settings, env loading, paths)         │             │
│  └────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Extract Constants (DONE)
Split `constants.py` into logical sub-modules with a re-export facade.
- `constants/tools.py`, `constants/urls.py`, `constants/llm.py`, etc.
- Maintains backward compatibility via `__init__.py` re-exports
- **Status**: Complete

### Phase 2: Extract Path Management from Settings (DONE)
Create `PathManager` class outside of `Settings`.
- Removes 15+ lines of path logic from the config class
- Reduces `Settings` from 345 to ~200 lines
- **Status**: Complete

### Phase 3: Dependency Injection Container
Introduce a lightweight DI container to replace global singletons.

```python
# src/fu7ur3pr00f/container.py
class Container:
    """Lightweight DI container for application services."""

    _instance: Container | None = None

    def __init__(self):
        self._settings = Settings()
        self._model_manager: ModelSelectionManager | None = None

    @classmethod
    def get(cls) -> Container:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def model_manager(self) -> ModelSelectionManager:
        if self._model_manager is None:
            self._model_manager = ModelSelectionManager()
        return self._model_manager

    def reset(self) -> None:
        """Reset all cached services (for testing and settings reload)."""
        self._model_manager = None
```

### Phase 4: Move Tool Imports to Module Level
With the DI container, tools can import dependencies at module level:

```python
# Before (lazy import)
@tool
def search_jobs(query: str) -> str:
    from fu7ur3pr00f.gatherers.market import JobMarketGatherer
    gatherer = JobMarketGatherer()
    ...

# After (module-level import)
from fu7ur3pr00f.gatherers.market import JobMarketGatherer
from fu7ur3pr00f.container import Container

@tool
def search_jobs(query: str) -> str:
    gatherer = JobMarketGatherer()
    ...
```

### Phase 5: Event-Based Tool Registration
For tools that depend on orchestrator state (e.g., `update_setting` calls `reset_orchestrator`):

```python
# Before (direct import)
def update_setting(key: str, value: str) -> str:
    from fu7ur3pr00f.agents.specialists.orchestrator import reset_orchestrator
    reset_orchestrator()

# After (event bus)
from fu7ur3pr00f.events import EventBus

def update_setting(key: str, value: str) -> str:
    EventBus.emit("settings_updated", key=key, value=value)

# In orchestrator.py:
EventBus.on("settings_updated", lambda **kwargs: reset_orchestrator())
```

### Phase 6: Eliminate Lazy Imports in base.py
Move `load_prompt` to module-level (already there), move `get_model` through DI:

```python
# Before
def _contribute_via_agent(self, ...):
    from fu7ur3pr00f.llm.model_selection import get_model
    model, _ = get_model(purpose="agent")

# After
from fu7ur3pr00f.container import Container

def _contribute_via_agent(self, ...):
    container = Container.get()
    model, _ = container.model_manager.get_model(purpose="agent")
```

## Risk Assessment

| Phase | Risk | Effort | Benefit |
|-------|------|--------|---------|
| 1. Constants | Low | Done | 100+ line file split |
| 2. PathManager | Low | Done | Config SRP |
| 3. DI Container | Medium | 2-3 days | Foundation for all future work |
| 4. Module-level imports | Low | 1 day | Cleaner code, fewer test patches |
| 5. Event bus | Medium | 2 days | Decoupled tool/orchestrator |
| 6. base.py cleanup | Low | 0.5 day | Consistent import style |

## Testing Strategy
Each phase must:
1. Pass all existing tests (551+ currently)
2. Add tests for new abstractions (Container, EventBus)
3. Update patch paths in existing tests
4. Run full suite + lint after each phase

## Timeline
- Phase 3 (DI Container): ~1 week
- Phase 4-5 (Event Bus + Module-level): ~1 week  
- Phase 6 (base.py cleanup): ~0.5 days
- **Total estimated**: 2-3 weeks for full refactor

## Current Status
Phases 1-2 complete. Phases 3-6 are planned but not yet scheduled.
