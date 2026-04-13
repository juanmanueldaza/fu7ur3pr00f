# Design: no-workarounds

## Architecture Decisions

### ADR-1: Fail loudly instead of fabricating safe-looking output

**Decision**: Remove defensive fallback branches that fabricate neutral-looking
values such as empty strings, empty lists, default provider names, or default
scores when the underlying operation has failed.

**Rationale**: These branches make the system lie about its state. In this
repository, fabricated values hide broken analysis, broken persistence, and
broken configuration while producing outputs that look valid enough to trust.
That directly conflicts with the project's explicit rule against dead fallback
code and silent workarounds.

**Implication**: The correct behavior at these boundaries is to raise a typed
error and let the caller fail fast.

---

### ADR-2: Existing exception hierarchy remains the truth boundary

**Decision**: Reuse the current exception taxonomy instead of introducing a new
cross-cutting error type.

**Rationale**:
- `AnalysisError` already communicates failed reasoning/synthesis boundaries.
- `NoDataError` already communicates missing required data.
- `ServiceError` already communicates infrastructure/configuration failures.

Keeping those exception types preserves call-site expectations while removing
the silent fallback behavior behind them.

---

### ADR-3: Fix type errors at the root, not with blanket suppressions

**Decision**: Eliminate bare `# type: ignore` comments by applying root-cause
typing fixes: assertions for runtime-narrowed values, `cast()` for protocol
adaptation, and more precise annotations for middleware and loop variables.

**Rationale**: Blanket ignores let real regressions accumulate invisibly.
Because this repository already treats `pyright` as a completion gate, the
cleanest design is to make the code truthful enough that the checker can pass
without suppression.

---

## Implementation Shape

### Error-propagation cleanup

- Remove broad exception swallowing in analysis, persistence, and UI save
  paths.
- Replace default-return branches with raised exceptions at validation or
  service boundaries.
- Preserve logging where it adds debugging value, but re-raise after logging.

### Type-safety cleanup

- Replace content-type assumptions with explicit assertions where model
  responses may be union-typed.
- Use `cast()` where external libraries expose protocols or dynamic objects
  that static analysis cannot infer precisely.
- Tighten annotations in middleware, diagnostics, and generators so the type
  checker can verify the control flow directly.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Surfaced exceptions break previously hidden paths | Medium | Medium | Add error-path tests for each affected boundary and run the full suite |
| External integrations return unexpected null-ish data | Medium | Medium | Validate at the parse/boundary layer instead of defaulting downstream |
| Type fixes reveal deeper library stubs issues | Low | Medium | Prefer small local assertions/casts over new global ignore comments |

---

## Sequence

```text
Failure occurs
  -> boundary detects it
  -> code raises typed exception
  -> tests assert propagation
  -> pyright/ruff/pytest verify no hidden workaround remains
```
