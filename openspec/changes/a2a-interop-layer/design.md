# Design: A2A-Native Interoperability Layer

## Technical Approach
Convert the internal blackboard orchestration into a standard A2A protocol-driven system. Specialists will be modeled as `A2AServers` and the orchestrator as an `A2AClient`. External agents (like PREA) will be treated as remote specialist nodes.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **SDK** | `a2a-sdk` | Official Linux Foundation standard. Provides Pydantic schemas, JSON-RPC handling, and FastAPI integration. |
| **Agent Registry** | Local Config + Discovery | Store known agent endpoints (local/remote) in `config.py`. Use `.well-known/agent.json` for initial handshake. |
| **Transport** | Hybrid (In-Process/HTTP) | Use HTTP for remote agents (PREA) and optimized in-process JSON-RPC for local specialists to minimize latency. |
| **Auth** | Interceptor Pattern | Use A2A SDK interceptors to inject `X-API-Key` or `Bearer` tokens based on the Agent Card security requirements. |

## Data Flow

```text
User ──→ CLI ──→ ConversationEngine (A2A Client)
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
    Local Specialists      External Agents (PREA)
    (A2A Server logic)     (Remote A2A Server)
           │                     │
           └──────────┬──────────┘
                      ▼
               Career Blackboard (Shared State)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modify | Add `a2a-sdk[http-server]`. |
| `src/fu7ur3pr00f/agents/specialists/a2a_adapter.py` | Create | Adapter to wrap `BaseAgent` into an `A2AServer`. |
| `src/fu7ur3pr00f/agents/blackboard/executor.py` | Modify | Use `ClientFactory` to invoke specialists instead of direct method calls. |
| `src/fu7ur3pr00f/chat/app.py` | Modify | Mount `A2AFastAPIApplication` at `/api/a2a`. |
| `public/agent.json` | Create | The official Agent Card for fu7ur3pr00f. |
| `src/fu7ur3pr00f/agents/specialists/external_proxy.py` | Create | Simple proxy for non-local A2A agents. |

## Interfaces / Contracts

### Outbound JSON-RPC Message
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "text": "Analyze job market for Senior Python Dev",
    "context": { "blackboard_id": "uuid-123" }
  },
  "id": "req-001"
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `A2AAdapter` | Mock `AgentExecutor` and verify JSON-RPC serialization. |
| Integration | End-to-end A2A Loop | Spin up a local `A2AServer` and call it with `ClientFactory`. |
| Security | Auth Interceptor | Verify `X-API-Key` is injected only for agents requiring it. |

## Migration / Rollout
1. Add SDK and basic `A2AProxy`.
2. Integrate PREA as the first external specialist.
3. Gradually move local specialists to the A2A adapter (versioned rollout).

## Open Questions
- [ ] Should we use gRPC for local specialists to further reduce latency? (Deferred: JSON-RPC is simpler for now).
- [ ] How to handle stateful context in A2A? (A2A v0.3.0 supports `context_id`).
