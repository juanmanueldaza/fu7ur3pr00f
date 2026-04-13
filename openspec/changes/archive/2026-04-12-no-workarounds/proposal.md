# Proposal: no-workarounds — Eliminate All Defensive Fallback Code

## Intent

The codebase contains 45 violations across 6 categories where errors are silently swallowed, hardcoded defaults mask failures, and `# type: ignore` comments hide type-safety gaps. These patterns directly contradict the project's core rule: no fallbacks, no hardcoded defaults, no silent overrides, no dead branches. Every violation is a place where the system lies about its state instead of failing loudly. This change removes all of them.

## Scope

### In Scope
- 8 HIGH-priority: exception swallowing, hardcoded fallback strings/providers, silent `or ""` defaults, bare `except: pass`
- 8 MEDIUM-priority: `or []`/`or ""` on required fields, `contextlib.suppress(Exception)`, bare `pass` on conversion errors, empty-string returns for missing config
- 3 LOW-priority: cleanup-before-reraise, country validation suppress, log-then-reraise
- 50+ `# type: ignore` comments replaced with proper type annotations or protocol fixes
- 1 Click compatibility shim (`_patch_click_make_metavar`) removed with version guard
- 1 optional-import pattern (`markdown = None`) replaced with hard dependency or feature gate

### Out of Scope
- New features or behavior changes visible to users
- Prompt content changes
- Test infrastructure changes (only test assertions updated to expect errors)

## Capabilities

### New Capabilities
None

### Modified Capabilities
None — pure code quality cleanup, no behavior changes at the spec level

## Approach

Work file-by-file in priority order (HIGH first). For each violation: (1) remove the fallback/suppress, (2) raise the appropriate exception from the project hierarchy (`NoDataError` for missing data, `AnalysisError` for failed analysis, `ServiceError` for infra), (3) add or fix type annotations to eliminate the corresponding `# type: ignore`, (4) update tests to assert the error is raised. The Click shim gets a version guard that errors on unsupported versions. The optional markdown import becomes a hard dependency in `pyproject.toml`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `agents/` | High | 6 files: values, blackboard graph/engine/conversation_graph, tools, middleware |
| `llm/` | High | model_selection hardcoded provider fallback |
| `mcp/` | Medium | jobspy 9x `or ""`, github/himalayas suppress patterns |
| `chat/` | Medium | screens.py bare except on credential save |
| `config.py`, `memory/` | Medium | Empty-string returns, null-YAML acceptance |
| `*.py` (type ignores) | Low | 50+ annotation fixes across 10+ files |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Surfaced errors break existing flows | Medium | Each fix adds a test proving the error path; run full suite per file |
| External API returns unexpected nulls | Medium | MCP client fields validated at parse boundary, not silently defaulted |
| `# type: ignore` removal reveals deeper type issues | Low | Run `pyright` incrementally; fix root causes, don't add new ignores |

## Rollback Plan

Each file is an independent commit. Revert any single commit without affecting others. No schema or data migrations involved.

## Dependencies

- Exception hierarchy (`ServiceError`, `NoDataError`, `AnalysisError`) must already exist — confirmed present
- `markdown` package added to hard dependencies in `pyproject.toml` (if optional-import pattern is removed)

## Success Criteria

- [ ] `pyright src/fu7ur3pr00f` produces 0 errors, 0 warnings, 0 informations
- [ ] `pytest tests/ -q` passes
- [ ] `ruff check .` passes
- [ ] Zero `# type: ignore` comments in codebase
- [ ] Zero `or <default>` fallbacks on required fields
- [ ] Zero `except Exception: pass` or `contextlib.suppress(Exception)` patterns
- [ ] Zero hardcoded fallback strings in agent output paths
