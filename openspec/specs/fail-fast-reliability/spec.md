# Spec: Fail-Fast Reliability and Type Safety

## Requirement: Failed operations do not return fabricated values

Production code MUST NOT hide failures by returning hardcoded neutral values or
substituting defaults for required data.

### Scenario: Analysis failure does not become a fake score

```text
Given  a scoring or synthesis routine encounters an exception
When   it cannot produce a truthful result
Then   the exception propagates
 And   no fabricated fallback score or narrative is returned
```

### Scenario: Missing required configuration does not default silently

```text
Given  a required provider or required field is missing
When   the validation boundary is reached
Then   the code raises a descriptive error
 And   it does not substitute an empty string, empty list, or default provider
```

## Requirement: Operational failures are not swallowed

The codebase MUST NOT use silent exception swallowing for persistence, prompt
construction, orchestration, or UI save flows where correctness depends on the
operation succeeding.

### Scenario: Persistence failure propagates to the caller

```text
Given  a profile or memory write fails
When   the write path runs
Then   an exception is raised
 And   the caller does not receive a false success response
```

## Requirement: Type safety is enforced without blanket ignores

The repository SHALL pass strict static analysis without bare `# type: ignore`
comments in production code.

### Scenario: Repository contains no bare type-ignore comments

```text
Given  the current src/ tree
When   scanning for bare "# type: ignore"
Then   zero matches are found
 And   pyright completes without errors, warnings, or informations
```
