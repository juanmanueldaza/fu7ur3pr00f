# Spec: no-workarounds

## Domain: Fail-Fast Reliability and Type Safety

### REQ-1 — No silent fallback behavior

**REQ-1.1** The codebase MUST NOT return hardcoded success-like values when an
operation fails and the failure changes the truthfulness of the result.

**REQ-1.2** Required fields and required computed values MUST NOT be replaced
with fallback literals such as `""`, `[]`, `{}`, or provider-name defaults in
order to keep execution moving.

**REQ-1.3** When an operation cannot produce a truthful result, the code MUST
raise an appropriate exception from the existing project hierarchy when
available (`ServiceError`, `NoDataError`, `AnalysisError`) or re-raise the
underlying exception when that is the correct boundary behavior.

---

### REQ-2 — No swallowed exceptions

**REQ-2.1** The codebase MUST NOT use `except Exception: pass` for operational
paths.

**REQ-2.2** The codebase MUST NOT use `contextlib.suppress(Exception)` for
write, persistence, analysis, or orchestration flows where failure affects user
visible correctness or system state.

**REQ-2.3** If an error is logged at a boundary that still requires failure
propagation, the code SHALL log and re-raise rather than log and continue with
fabricated success.

---

### REQ-3 — Strict typing over ignore comments

**REQ-3.1** Bare `# type: ignore` comments MUST NOT remain in the production
codebase.

**REQ-3.2** Type errors MUST be resolved through root-cause fixes such as
assertions, casts, protocols, or narrower annotations.

**REQ-3.3** If a type ignore is ever unavoidable in the future, it SHOULD be
scoped to a specific error code and documented at the exact callsite.

---

### REQ-4 — Verification gates

**REQ-4.1** The repository MUST pass `pyright src/fu7ur3pr00f` with zero
errors, zero warnings, and zero informations before this change is considered
complete.

**REQ-4.2** The repository MUST pass `ruff check .`.

**REQ-4.3** The repository MUST pass `pytest tests/ -q`.

**REQ-4.4** Verification MUST include an explicit audit proving that no bare
`# type: ignore` comments remain in `src/`.

---

## Scenarios

### Scenario 1 — Analysis failure propagates

```text
Given  a scoring or synthesis path encounters an unexpected exception
When   the operation cannot produce a truthful result
Then   the code raises an exception
 And   it does not return a fabricated score, summary, or fallback payload
```

### Scenario 2 — Persistence failure propagates

```text
Given  a profile or memory write fails
When   the write path executes
Then   the operation raises an exception
 And   it does not report success to the caller
```

### Scenario 3 — Required values are not defaulted

```text
Given  a required provider or required field is missing
When   the code reaches the validation boundary
Then   the code raises a descriptive error
 And   it does not substitute a default provider, empty string, or empty list
```

### Scenario 4 — Type safety enforced without ignores

```text
Given  the repository after this change
When   scanning src/ for bare "# type: ignore"
Then   zero matches are found
 And   static type checking passes without suppressing unknown issues
```
