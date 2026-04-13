# Tasks: no-workarounds

## Phase 1 — HIGH Priority Fallbacks

- [x] **P1-1** `values.py`: Delete `except Exception: return {"score": 50, ...}` in score evaluation; let exception propagate.
- [x] **P1-2** `conversation_graph.py`: Replace `except Exception: suggestions = []` with `raise AnalysisError(...)`.
- [x] **P1-3** `graph.py`: Raise `AnalysisError` when specialist data is absent; remove all `or ""` on required fields.
- [x] **P1-4** `model_selection.py`: Replace `or "azure"` fallback with `raise ServiceError("No LLM provider configured")`.
- [x] **P1-5** `memory/profile.py`: Raise `ServiceError` on corrupt or empty YAML instead of returning an empty profile.
- [x] **P1-6** `engine.py`: Remove dead `or []` / `or ""` on `UserProfile` fields (guaranteed non-None by `field(default_factory=...)`).
- [x] **P1-7** `chat/screens.py`: Remove `except Exception: pass` on credential save; let the error surface.

## Phase 2 — MEDIUM Priority (Suppress/Silence Removal)

- [x] **P2-1** `agents/tools/github.py`: Remove `contextlib.suppress(Exception)` around profile save; raise on failure.
- [x] **P2-2** `agents/middleware/dynamic_prompt.py`: Replace `contextlib.suppress` with a logged error and re-raise.
- [x] **P2-3** `agents/tools/memory.py`: Storage failure must raise instead of returning a success string.

## Phase 3 — Type Fixes (Remove All `# type: ignore`)

- [x] **P3-1** `turn_classifier.py`: Replace `# type: ignore` with `assert isinstance(result.content, str)`.
- [x] **P3-2** `agents/specialists/routing.py`: Assert result is not None before accessing `.specialists`; remove ignore.
- [x] **P3-3** `agents/specialists/base.py`: Assert or cast structured-output result; remove ignore.
- [x] **P3-4** `agents/tools/_analysis_helpers.py`: Assert content type; remove ignore.
- [x] **P3-5** `agents/middleware/analysis_synthesis.py`: Add proper type annotations; remove ignore.
- [x] **P3-6** `gatherers/cv.py`: Assert content type; remove ignore.
- [x] **P3-7** `memory/embeddings.py`: Use `cast()` for chromadb protocol; remove ignore.
- [x] **P3-8** `diagnostics.py`: Fix loop variable typing; remove ignore.
- [x] **P3-9** `generators/cv_generator.py`: Narrow any remaining ignore to a specific error code or fix root cause.
- [x] **P3-10** `cli.py`: Fix type annotations on compat shim or remove shim if Click version allows.
- [x] **P3-11** Audit remaining files: replace every bare `# type: ignore` with a specific error code or root fix.

## Phase 4 — Tests and Verification

- [x] **P4-1** Add error-path tests for each P1 task: assert the correct exception type propagates (no silent swallow).
- [x] **P4-2** Add error-path tests for each P2 task: assert failure raises instead of silently continuing.
- [x] **P4-3** Run `pyright src/fu7ur3pr00f` — must report 0 errors, 0 warnings, 0 informations.
- [x] **P4-4** Run `pytest tests/ -q` — full suite must pass.
- [x] **P4-5** Run `ruff check .` — zero violations.
- [x] **P4-6** Confirm zero bare `# type: ignore` remain in codebase (`grep -rn "# type: ignore$" src/`).
