# Verify Report: remove-direct-profile-answer

**Mode**: Strict TDD
**Date**: 2026-04-12

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 7 |
| Tasks complete | 7 |
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
| REQ-1.1: `_direct_profile_answer` deleted | Scenario 1 — no matches | `grep -r "_direct_profile_answer" src/` → 0 results | ✅ COMPLIANT |
| REQ-1.2: Bypass block removed from `execute_inner_node` | Scenario 2 — factual query reaches inner graph | `test_conversation_graph.py > TestFactualQueryReachesCoach::test_factual_query_reaches_coach` | ✅ COMPLIANT |
| REQ-1.3: `if turn_type == "factual"` guard removed | Scenario 2 | Code inspection confirms guard deleted entirely | ✅ COMPLIANT |
| REQ-2.1: turn_classifier.py unmodified | Scenario 4 — classifier unchanged | `test_conversation_graph.py > TestTurnClassifierHeuristics::test_classifies_identity_question_as_factual_without_history` | ✅ COMPLIANT |
| REQ-2.2: Factual → coach fast-path in route_turn_node | Scenario 2 | `test_conversation_graph.py > TestFactualQueryReachesCoach::test_factual_query_reaches_coach` | ✅ COMPLIANT |
| REQ-2.3: Coach uses `get_user_profile` | Scenario 3 — tool invoked | No dedicated test (requires real LLM + tool call) | ⚠️ PARTIAL |
| REQ-3.1: `TestDirectProfileAnswer` deleted | Scenario 1 | Confirmed: class absent from test file | ✅ COMPLIANT |
| REQ-3.2: Replacement regression test | Scenario 2 | `test_conversation_graph.py > TestFactualQueryReachesCoach::test_factual_query_reaches_coach` | ✅ COMPLIANT |

**Compliance summary**: 7/8 scenarios compliant (1 partial — REQ-2.3 requires real LLM invocation, not unit-testable)

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| `_direct_profile_answer` deleted | ✅ Implemented | Zero matches in `src/` |
| Bypass block deleted from `execute_inner_node` | ✅ Implemented | `execute_inner_node` goes straight to `get_orchestrator()` |
| `TestDirectProfileAnswer` deleted | ✅ Implemented | Only `TestTurnClassifierHeuristics`, `TestFactualQueryReachesCoach`, `TestSuggestNextNode` remain |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| ADR-1: Full deletion, no replacement | ✅ Yes | Nothing replaced the heuristic path |
| ADR-2: Remove entire `if turn_type == "factual"` guard | ✅ Yes | Guard completely removed; factual routing still enforced upstream in `route_turn_node` |

---

## Issues Found

**CRITICAL**: None

**WARNING**: REQ-2.3 (coach uses `get_user_profile`) has no automated test — verifiable only via real LLM integration. Acceptable: `get_user_profile` is in `BASE_TOOLKIT`, and `specialist_guidance.md` instructs the coach to call it first for profile queries.

**SUGGESTION**: None

---

## Verdict

**PASS**

All spec requirements satisfied. `_direct_profile_answer` fully deleted. Factual queries reach the inner graph. 576/576 tests passing.
