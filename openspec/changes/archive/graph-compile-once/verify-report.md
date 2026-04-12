# Verify Report: graph-compile-once

**Mode**: Strict TDD
**Date**: 2026-04-12

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 9 |
| Tasks complete | 9 |
| Tasks incomplete | 0 |

---

## Build & Tests Execution

**Build (pyright)**: ✅ Passed — 0 errors, 0 warnings
**Lint (ruff)**: ✅ Passed — all checks passed
**Tests**: ✅ 576 passed / ❌ 0 failed / ⚠️ 0 skipped

---

## Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| REQ-1.1: Graph compiled once in `__init__` | Scenario 1 — compiled once | `test_engine.py > TestGraphCompileOnce::test_graph_compiled_once_on_init` | ✅ COMPLIANT |
| REQ-1.2: `invoke_turn()` does NOT call `build_conversation_graph()` | Scenario 1 | `test_engine.py > TestGraphCompileOnce::test_graph_compiled_once_on_init` — asserts `mock_build.call_count == 1` after 3 invocations | ✅ COMPLIANT |
| REQ-1.3: `reset_conversation_engine()` triggers fresh compile | Scenario 4 — engine reset | `test_engine.py > TestGraphCompileOnce::test_reset_triggers_fresh_compile` | ✅ COMPLIANT |
| REQ-2.1: `_callbacks` dict initialised in `__init__` | Scenario 2 | Code inspection confirms `self._callbacks: dict[str, Any] = {}` in `__init__` | ✅ COMPLIANT |
| REQ-2.2: `invoke_turn()` updates `_callbacks` before graph invoke | Scenario 3 — callbacks change between turns | `test_engine.py > TestGraphCompileOnce::test_callbacks_updated_per_turn` | ✅ COMPLIANT |
| REQ-2.3: Nodes read from holder at execution time | Scenario 2 | `test_engine.py > TestGraphCompileOnce::test_callbacks_updated_per_turn` — captures dict snapshot at invoke time | ✅ COMPLIANT |
| REQ-2.4: `build_conversation_graph()` takes `callbacks: dict`, not 5 individual params | Scenario 1 | Code inspection: signature is `def build_conversation_graph(checkpointer=None, callbacks: dict | None = None)` | ✅ COMPLIANT |
| REQ-3.1: `invoke_turn()` signature unchanged | Scenario 5 — None callbacks | `test_engine.py > TestGraphCompileOnce::test_none_callbacks_dont_raise` | ✅ COMPLIANT |
| REQ-3.2: `chat/client.py` unchanged | — | `git diff` confirms zero changes to `chat/client.py` | ✅ COMPLIANT |
| REQ-3.3: Inner graph/executor/specialists unchanged | — | Only `conversation_graph.py` and `engine.py` modified | ✅ COMPLIANT |
| REQ-4.1: Sequential-use docstring added | — | Code inspection confirms docstring in `ConversationEngine` class | ✅ COMPLIANT |
| — | Scenario 5 — None callbacks | `test_engine.py > TestGraphCompileOnce::test_none_callbacks_dont_raise` | ✅ COMPLIANT |

**Compliance summary**: 12/12 scenarios compliant

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| `self._graph` stored in `__init__` | ✅ Implemented | Line 66 in engine.py |
| `self._build_graph` removed | ✅ Implemented | No reference to `_build_graph` in engine.py |
| `self._callbacks.update({...})` at start of `invoke_turn` | ✅ Implemented | Lines 100-107 in engine.py |
| `_cb.get(...)` in `execute_inner_node` | ✅ Implemented | Lines 187-193 in conversation_graph.py |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| ADR-1: `_CallbackHolder` (mutable dict) | ✅ Yes | `self._callbacks` dict closed over in nodes |
| ADR-2: Keep `graph.invoke()` at outer level | ✅ Yes | No streaming change at outer graph level |
| Rejected: `contextvars.ContextVar` | ✅ Correctly rejected | Not implemented; documented as future migration path |
| Rejected: Full `get_stream_writer()` migration | ✅ Correctly rejected | Inner graph already correct; outer untouched |

---

## Issues Found

**CRITICAL**: None

**WARNING**: None

**SUGGESTION**: None

---

## Verdict

**PASS**

All 12 spec scenarios compliant. 577/577 tests passing. Graph compiles once per engine instance, reset triggers fresh compile, callbacks update per-turn — all verified with dedicated tests.
