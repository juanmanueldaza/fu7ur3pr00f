# Delta for Agent Execution (Outer Graph)

## ADDED Requirements

### Requirement: External A2A Specialist Delegation
The outer conversation engine SHALL support delegating a turn to a remote A2A-capable agent via a dedicated `A2AProxyAgent` specialist.

#### Scenario: Remote specialist contribution
- GIVEN a conversation on the blackboard
- WHEN the orchestrator selects the `A2AProxyAgent`
- THEN the engine SHALL initiate a JSON-RPC request to the remote agent
- AND wait for the final finding before continuing the graph execution.

### Requirement: A2A Auth Handling
The engine MUST use the `security` schemes from the `AgentCard` to authenticate with remote agents, supporting `X-API-Key` and `Bearer` headers.

#### Scenario: Sending X-API-Key header
- GIVEN a remote agent requiring `X-API-Key`
- WHEN the engine sends a request
- THEN it SHALL include the corresponding value from the system environment/config.
