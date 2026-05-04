# Proposal: A2A Interoperability Layer

## Intent
Enable fu7ur3pr00f to communicate with external agents following the A2A Protocol (v0.3.0). This addresses the need for specialized external insights (e.g., PREA's Constraint Discovery) and establishes the project as an interoperable agentic system.

## Scope

### In Scope
- Integration of `a2a-sdk[http-server]` in `pyproject.toml`.
- **Inbound**: FastAPI endpoint at `/api/a2a` to receive JSON-RPC messages.
- **Outbound**: `A2AProxyAgent` specialist to delegate tasks to external agents.
- **Discovery**: Static `agent.json` (Agent Card) at `/.well-known/agent.json`.
- **Security**: Auth interceptor for `X-API-Key` support.

### Out of Scope
- Automatic agent discovery via crawler (manual discovery/connection for now).
- Complex multi-agent negotiation protocols (beyond basic task delegation).

## Capabilities

### New Capabilities
- `a2a-interop`: Standardized agent-to-agent communication via JSON-RPC.
- `agent-discovery`: Capability to be discovered and to discover others via Agent Cards.

### Modified Capabilities
- `agent-execution-outer-graph`: Orchestrator will now support `A2AProxyAgent` as a valid specialist destination.

## Approach
1. Add `a2a-sdk` dependency.
2. Implement `A2AProxyAgent(BaseAgent)` using `ClientFactory`.
3. Configure `A2AFastAPIApplication` in `src/fu7ur3pr00f/chat/app.py` or a dedicated service.
4. Define the project's `AgentCard` with its 5 local specialists as skills.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pyproject.toml` | Modified | Add `a2a-sdk[http-server]` dependency. |
| `src/fu7ur3pr00f/agents/specialists/` | New | Add `a2a_proxy.py` (Outbound client). |
| `src/fu7ur3pr00f/chat/app.py` | Modified | Mount A2A FastAPI application (Inbound server). |
| `public/` or root | New | Add `agent.json` for discovery. |
| `src/fu7ur3pr00f/utils/security.py` | Modified | Add A2A auth header sanitization/validation. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Remote agent latency | High | Strict timeouts (30s) and fallback to local specialists. |
| Malicious Agent Cards | Med | Strict Pydantic validation of discovered cards. |
| API Key leakage | Low | Use existing `.env` (0o600) and `security.py` sanitization. |

## Rollback Plan
Remove `a2a-sdk` from `pyproject.toml` and delete `a2a_proxy.py`. The orchestrator handles missing specialists gracefully by skipping them if not registered.

## Dependencies
- `a2a-sdk[http-server]>=0.3.0`
- `httpx` (for the interceptors)

## Success Criteria
- [ ] `fu7ur3pr00f` responds to JSON-RPC calls at `/api/a2a`.
- [ ] `A2AProxyAgent` can successfully call PREA's endpoint with an API Key.
- [ ] `agent.json` is valid according to the A2A v0.3.0 schema.
