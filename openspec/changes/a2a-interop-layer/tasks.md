# Tasks: A2A Interoperability Layer

## Phase 1: Foundation & Infrastructure

- [ ] 1.1 Add `a2a-sdk[http-server]>=0.3.0` to `pyproject.toml` dependencies.
- [ ] 1.2 Update `src/fu7ur3pr00f/config.py` to include `A2A_AGENT_KEY` for PREA.
- [ ] 1.3 Create `src/fu7ur3pr00f/agents/specialists/a2a_types.py` for shared Pydantic A2A models.
- [ ] 1.4 Create `public/.well-known/agent-card.json` (and symlink `agent.json`) with basic metadata.

## Phase 2: Inbound A2A Server

- [ ] 2.1 Implement `A2AHandler` in `src/fu7ur3pr00f/agents/blackboard/a2a_handler.py` to route JSON-RPC to `ConversationEngine`.
- [ ] 2.2 Configure `A2AFastAPIApplication` in `src/fu7ur3pr00f/chat/app.py`.
- [ ] 2.3 Add `/api/a2a` route and verify `.well-known/agent-card.json` accessibility.

## Phase 3: Outbound A2A Client (PREA Integration)

- [ ] 3.1 Implement `PreaAuthInterceptor` in `src/fu7ur3pr00f/agents/specialists/a2a_interceptors.py` for `X-API-Key`.
- [ ] 3.2 Create `A2AProxyAgent` in `src/fu7ur3pr00f/agents/specialists/a2a_proxy.py` using `ClientFactory`.
- [ ] 3.3 Register `A2AProxyAgent` in `src/fu7ur3pr00f/agents/specialists/__init__.py`.

## Phase 4: Integration & Testing

- [ ] 4.1 Write `tests/test_a2a_serialization.py` for JSON-RPC message/send mapping.
- [ ] 4.2 Write `tests/test_a2a_server.py` using FastAPI `TestClient` to verify inbound routing.
- [ ] 4.3 Write `tests/test_prea_proxy.py` with mocked remote endpoint to verify auth interceptor.
- [ ] 4.4 Verify Scenario: "Successful outbound message" from `a2a-interop` spec.
- [ ] 4.5 Verify Scenario: "Handling 401 Unauthorized" from `a2a-interop` spec.

## Phase 5: Cleanup & Documentation

- [ ] 5.1 Update `README.md` with A2A Interoperability notes.
- [ ] 5.2 Remove `scripts/test_prea_a2a.py` (temporary probe).
