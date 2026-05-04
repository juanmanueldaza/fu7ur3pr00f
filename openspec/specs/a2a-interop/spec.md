# A2A Interop Specification

## Purpose
Standardize communication between fu7ur3pr00f and external AI agents using the A2A Protocol (v0.3.0).

## Requirements

### Requirement: JSON-RPC Message Handling
The system MUST process inbound and outbound A2A messages using the JSON-RPC 2.0 format as specified by the A2A SDK.

#### Scenario: Successful outbound message to external agent
- GIVEN a configured A2A client with a valid endpoint and API Key
- WHEN the orchestrator delegates a task to the `A2AProxyAgent`
- THEN the system SHALL send a JSON-RPC `message/send` request
- AND the remote response SHALL be mapped to a `SpecialistFinding` on the blackboard.

#### Scenario: Handling 401 Unauthorized from remote agent
- GIVEN an A2A client with an invalid or missing API Key
- WHEN a message is sent to the remote agent
- THEN the system SHALL catch the 401 error
- AND record a failure finding on the blackboard indicating "Unauthorized".

### Requirement: A2A Task Lifecycle Support
The system SHALL support the A2A task lifecycle (create, query, cancel) for long-running specialist tasks.

#### Scenario: Querying task status
- GIVEN an active A2A task ID
- WHEN the system requests task updates
- THEN it SHALL use the JSON-RPC `task/get` method
- AND update the blackboard state with the latest progress.

### Requirement: Inbound A2A Server
The system SHALL expose a FastAPI endpoint at `/api/a2a` to receive and process A2A requests from external agents.

#### Scenario: External agent sends a message
- GIVEN the fu7ur3pr00f A2A server is running
- WHEN an external agent sends a valid JSON-RPC message to `/api/a2a`
- THEN the system SHALL route the query to the `ConversationEngine`
- AND return a JSON-RPC response with the processing result.
