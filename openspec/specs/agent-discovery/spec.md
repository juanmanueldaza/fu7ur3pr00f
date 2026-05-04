# Agent Discovery Specification

## Purpose
Enable automated agent discovery via standardized metadata (Agent Cards).

## Requirements

### Requirement: Expose Agent Card (agent.json)
The system MUST host a valid `AgentCard` at `/.well-known/agent.json` exposing the agent's name, version, and skills.

#### Scenario: Validating fu7ur3pr00f Agent Card
- GIVEN a request to `/.well-known/agent.json`
- WHEN the system responds
- THEN the content SHALL be valid JSON according to the A2A v0.3.0 schema
- AND include the `skills` available (e.g., Coach, Jobs, Learning, Code, Founder).

### Requirement: Remote Agent Discovery
The system SHALL have the capability to fetch and parse an `AgentCard` from a remote URI to determine its capabilities.

#### Scenario: Fetching PREA's Agent Card
- GIVEN a URI for a remote agent
- WHEN the system requests its Agent Card
- THEN it SHALL parse the `skills` and `security` requirements from the remote `agent.json`.
