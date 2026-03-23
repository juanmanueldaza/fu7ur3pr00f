# Configuration

## Quick Start

Run `/setup` in the chat client to configure interactively, or edit `~/.fu7ur3pr00f/.env` manually.

## LLM Provider

Pick **ONE** provider. Auto-detected from available keys if not specified.

| Provider | Variable | Notes |
|----------|----------|-------|
| FutureProof Proxy | `FUTUREPROOF_PROXY_KEY` | Default, zero config, free starter tokens |
| OpenAI | `OPENAI_API_KEY` | Requires OpenAI account |
| Anthropic | `ANTHROPIC_API_KEY` | Requires Anthropic account |
| Google | `GOOGLE_API_KEY` | Gemini models |
| Azure | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` | Azure OpenAI Service |
| Ollama | `OLLAMA_BASE_URL` | Local, offline, free |

### Example

```bash
# ~/.fu7ur3pr00f/.env

# Option 1: FutureProof Proxy (recommended for getting started)
FUTUREPROOF_PROXY_KEY=fp-...

# Option 2: OpenAI
OPENAI_API_KEY=sk-...

# Option 3: Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
```

## Purpose-Based Model Routing

Override the default fallback chain for specific purposes:

```bash
AGENT_MODEL=gpt-4o-mini        # Tool calling
ANALYSIS_MODEL=gpt-4.1         # Analysis / CV generation
SUMMARY_MODEL=gpt-4o-mini      # Summarization
SYNTHESIS_MODEL=o4-mini        # Synthesis (reasoning)
EMBEDDING_MODEL=text-embedding-3-small
```

## MCP Configuration

### GitHub MCP

```bash
# Create token at: https://github.com/settings/tokens
# Required scopes: repo, read:user, user:email
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
```

### GitLab

GitLab uses `glab` CLI for authentication:

```bash
# Install: https://gitlab.com/gitlab-org/cli
glab auth login
```

## Market Intelligence

Most sources require no configuration (JobSpy, HN, RemoteOK, etc.).

### Tavily Search

For salary data and market research:

```bash
# Get free key at: https://tavily.com/ (1,000 queries/month)
TAVILY_API_KEY=...
```

## Knowledge Base

```bash
# Auto-index career data after gathering
KNOWLEDGE_AUTO_INDEX=true

# Chunking for RAG
KNOWLEDGE_CHUNK_MAX_TOKENS=500
KNOWLEDGE_CHUNK_MIN_TOKENS=50
```

## Full Reference

See `.env.example` for all available options.

## File Permissions

The `/setup` wizard stores secrets with `0o600` permissions:

```bash
ls -la ~/.fu7ur3pr00f/.env
# -rw------- 1 user user ...
```

## Troubleshooting

### Provider not detected

1. Check variable names match exactly
2. Restart the chat client
3. Run `fu7ur3pr00f --debug` for verbose logs

### MCP not working

1. Verify tokens are set in `.env`
2. Check `~/.config/fu7ur3pr00f/.mcp.json`
3. Run `fu7ur3pr00f --debug` and look for MCP errors

## See Also

- [Architecture](architecture.md)
- [README](../README.md)
