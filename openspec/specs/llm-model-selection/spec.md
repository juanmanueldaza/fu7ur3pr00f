# Spec: LLM Model Selection

## Requirement: Provider availability is checked before model creation

Model selection MUST determine whether each provider is configured before trying
to initialize a model from that provider.

### Scenario: Unconfigured provider is skipped

```text
Given  the first chain entry uses a provider with missing credentials
When   get_model() evaluates the chain
Then   that entry is skipped
 And   model creation is not attempted for it
```

## Requirement: Model-selection walks the configured chain in order

`ModelSelectionManager.get_model()` MUST iterate through the effective chain in
order, stopping at the first successfully created model.

### Scenario: First configured provider succeeds

```text
Given  the first chain entry is configured and can be created
When   get_model() runs
Then   that model is returned immediately
 And   later entries are not attempted
```

### Scenario: First entry fails and second succeeds

```text
Given  the first chain entry is configured but model creation raises
 And   the second chain entry is configured and valid
When   get_model() runs
Then   the first failure is logged
 And   the second model is returned
```

## Requirement: Exhausted chains fail explicitly

If no model in the effective chain can be used, model selection MUST raise a
RuntimeError that guides the operator to check provider configuration and model
availability.

### Scenario: All entries are unavailable

```text
Given  every configured-chain entry is either unconfigured or fails creation
When   get_model() exhausts the chain
Then   a RuntimeError is raised
 And   the message includes guidance to check API keys or provider availability
```
