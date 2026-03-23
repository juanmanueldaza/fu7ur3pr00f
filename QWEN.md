# FutureProof - Project Context

## Project Overview

**FutureProof** is a career intelligence agent that gathers professional data, analyzes career trajectories, searches job boards, and generates ATS-optimized CVs through a conversational chat interface. Built with LangChain, LangGraph, and ChromaDB.

### Key Capabilities

- **Career Data Gathering**: LinkedIn CSV, GitHub (MCP), GitLab (glab CLI), portfolio websites, CliftonStrengths PDF
- **Job Search**: Queries 7 job boards + Hacker News hiring threads via JobSpy and MCP
- **Career Analysis**: Skill gap analysis, market trend analysis, career trajectory planning
- **CV Generation**: ATS-optimized CVs in Markdown and PDF (via WeasyPrint)
- **RAG Memory**: ChromaDB for knowledge base and episodic memory

### Architecture Highlights

- **Single Agent Design**: One agent with 40+ tools (multi-agent handoffs proved unreliable)
- **Database-First Pipeline**: Gatherers index directly to ChromaDB (no intermediate files)
- **Two-Pass Synthesis**: `AnalysisSynthesisMiddleware` for focused synthesis from reasoning models
- **Multi-Provider LLM Fallback**: Supports OpenAI, Anthropic, Google, Azure, Ollama, FutureProof proxy
- **HITL Confirmation**: LangGraph `interrupt()` for destructive/expensive operations

## Building and Running

### Installation

```bash
# Development install
pip install -e .

# Install dev tools
pip install pyright pytest ruff
```

### Running the Application

```bash
fu7ur3pr00f           # Launch chat client
fu7ur3pr00f --debug   # Verbose logging
```

### Testing and Quality

```bash
pytest tests/ -q            # Run unit tests
pyright src/fu7ur3pr00f     # Type checking
ruff check .                # Lint
ruff check . --fix          # Auto-fix lint issues
```

### Fresh Install Verification

```bash
scripts/fresh_install_check.sh --source local --config-from .env
```

## Project Structure

```
src/fu7ur3pr00f/
├── agents/
│   ├── career_agent.py     # Single agent with 40 tools, singleton cache
│   ├── middleware.py        # Dynamic prompts, synthesis, tool repair, summarization
│   ├── orchestrator.py      # LangGraph Functional API for analysis workflows
│   ├── helpers/             # Orchestrator support (data pipeline, LLM invoker)
│   └── tools/               # 40 tools by domain
│       ├── profile.py       # Profile management
│       ├── gathering.py     # Data gathering tools
│       ├── analysis.py      # Career analysis tools
│       ├── generation.py    # CV generation
│       ├── knowledge.py     # Knowledge base search
│       ├── market.py        # Market intelligence
│       ├── memory.py        # Episodic memory
│       ├── settings.py      # Settings management
│       ├── github.py        # GitHub MCP tools
│       ├── gitlab.py        # GitLab CLI tools
│       └── financial.py     # Financial tools
├── chat/
│   └── client.py            # Streaming chat client, HITL loop, Rich UI, /setup wizard
├── gatherers/               # LinkedIn CSV, CliftonStrengths PDF, portfolio scraper
├── generators/              # CV generation (Markdown + PDF via WeasyPrint)
├── llm/
│   └── fallback.py          # FallbackLLMManager: multi-provider, purpose-based routing
├── memory/
│   ├── checkpointer.py      # LangGraph checkpointing
│   └── chroma/              # ChromaDB RAG and episodic memory
├── mcp/
│   ├── factory.py           # MCP client factory
│   └── clients/             # 12 MCP clients (GitHub, Tavily, JobSpy, HN, etc.)
├── prompts/                 # System + analysis + CV prompt templates
├── services/                # GathererService, AnalysisService, KnowledgeService
└── utils/
    ├── console.py           # Rich console output
    ├── logging.py           # Logging setup
    ├── security.py          # PII anonymization, SSRF protection
    └── data_loader.py       # Data loading utilities
```

## Configuration

### Environment Variables

Configuration is stored in `~/.fu7ur3pr00f/.env` (created via `/setup` wizard). See `.env.example` for reference.

**LLM Provider** (pick ONE, auto-detected if empty):
- `FUTUREPROOF_PROXY_KEY` - FutureProof proxy (default, zero config)
- `OPENAI_API_KEY` - OpenAI
- `ANTHROPIC_API_KEY` - Anthropic
- `GOOGLE_API_KEY` - Google Gemini
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, etc. - Azure
- `OLLAMA_BASE_URL` - Ollama (local)

**Purpose-Based Routing** (optional overrides):
- `AGENT_MODEL` - Tool calling
- `ANALYSIS_MODEL` - Analysis / CV generation
- `SUMMARY_MODEL` - Summarization
- `SYNTHESIS_MODEL` - Synthesis (reasoning)
- `EMBEDDING_MODEL` - Embeddings

**Optional Integrations**:
- `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub MCP
- `TAVILY_API_KEY` - Tavily search (salary data, market research)
- `PORTFOLIO_URL` - Portfolio to scrape

### External Dependencies

Some features require system packages:

```bash
# GitLab tools
sudo apt-get install glab

# CliftonStrengths PDF import
sudo apt-get install poppler-utils

# PDF generation (CV export)
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libfontconfig1 libgdk-pixbuf-2.0-0
```

## Development Conventions

### Coding Style

- **Python 3.13** with type hints throughout
- **Line length**: 100 (enforced by ruff in `pyproject.toml`)
- **Imports**: Prefer `collections.abc` types (`Mapping`, `Sequence`) over `typing`
- **Error handling**: Raise exceptions (`ServiceError`, `NoDataError`, `AnalysisError`) instead of returning error dicts
- **Dependency injection**: Used for services to keep tests isolated

### Testing Practices

- **Framework**: `pytest` with fixtures in `tests/conftest.py`
- **Mocking**: Mock external services (LLMs, HTTP, ChromaDB) - no real API calls in unit tests
- **Test structure**: Tests mirror source structure (e.g., `tests/gatherers/` for `src/fu7ur3pr00f/gatherers/`)

### Commit Guidelines

- Conventional commits with concise subject
- Add short body when why/impact is non-obvious
- **No AI attribution lines** (no `Co-Authored-By` or "Generated by ...")

### Security Considerations

- PII is anonymized before sending to LLMs (see `utils/security.py`)
- Portfolio fetchers enforce SSRF protections (no private IP access)
- Secrets stored with `0o600` permissions in `~/.fu7ur3pr00f/.env`

## Dependency Notes

### NumPy Pinning

`python-jobspy` pins `numpy==1.26.3`. If your wider toolchain requires `numpy>=2.1`, use a separate virtual environment.

```bash
pip check  # Verify consistent NumPy version
```

### Build Artifacts

Clean stale artifacts with:

```bash
scripts/clean_dev_artifacts.sh
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata, dependencies, ruff/pytest config |
| `pyrightconfig.json` | Type checking configuration |
| `.env.example` | Environment variable reference |
| `AGENTS.md` | Repository guidelines for AI assistants |
| `tests/conftest.py` | Shared pytest fixtures |
| `src/fu7ur3pr00f/config.py` | Settings loading and validation |
| `src/fu7ur3pr00f/diagnostics.py` | Fresh install connectivity checks |

## Chat Commands

The CLI provides an interactive chat with built-in commands:

- `/setup` - Configure LLM provider and settings
- `/help` - Show all available commands
- `/gather` - Gather career data
- `/analyze` - Analyze career alignment
- `/search` - Search job boards
- `/generate` - Generate CV
- `/memory` - Query knowledge base
