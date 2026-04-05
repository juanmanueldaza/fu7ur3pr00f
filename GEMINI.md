# fu7ur3pr00f — Project Context & Guidelines

fu7ur3pr00f is a career intelligence system that gathers professional data, searches job boards, analyzes career alignment, and generates ATS-optimized CVs through a conversational AI interface.

## 🏗️ Architecture Overview

The system uses a sophisticated multi-agent orchestration pattern based on **LangGraph** and the **Blackboard Pattern**.

-   **Conversational Engine**: Managed by `ConversationEngine` using a persistent LangGraph workflow. It classifies turns (factual, follow-up, new query) and routes them accordingly.
-   **Blackboard Pattern**: Queries are routed to specialized agents (Specialists) who contribute findings to a shared blackboard. A final synthesis step compiles these findings into a coherent response.
-   **Memory & RAG**: Uses **ChromaDB** for vector-based knowledge (RAG) and episodic memory. Conversation history is persisted via a thread-based checkpointer.
-   **MCP Integration**: Integrates with 12 **Model Context Protocol (MCP)** clients for real-time data from GitHub, LinkedIn, job boards (JobSpy, Himalayas, etc.), and search engines (Tavily).
-   **Data Gatherers**: Modular gatherers for LinkedIn ZIP exports, CliftonStrengths PDFs, CVs (PDF/MD/TXT), and portfolios, indexing directly into ChromaDB.
-   **Offline Fallbacks**: Routing falls back to deterministic keyword scoring, and CV parsing falls back to local heading extraction when LLM calls are unavailable.

## 🛠️ Building and Running

### Development Setup
```bash
# Clone and install in editable mode
git clone https://github.com/juanmanueldaza/fu7ur3pr00f.git
cd fu7ur3pr00f
pip install -e .

# Install dev dependencies
pip install pyright pytest ruff
```

### Running the Application
```bash
# Start the interactive chat
fu7ur3pr00f

# Run with debug logs
fu7ur3pr00f --debug
```

### Testing & Validation
```bash
# Run all tests (quiet mode)
pytest tests/ -q

# Run benchmarks
pytest tests/benchmarks/ -v

# Type checking
pyright src/fu7ur3pr00f

# Linting
ruff check .
ruff check . --fix
```

### Build Scripts
Located in `scripts/`:
- `build_deb.sh`: Generates a Debian package.
- `fresh_install_check.sh`: Validates `pipx` installation.
- `validate_apt_artifact.sh`: Tests the `.deb` package in Docker.

## 📏 Development Conventions

### Python Standards
- **Version**: Requires **Python 3.13+**.
- **Imports**: Use `collections.abc` for generic types (e.g., `Sequence`, `Mapping`), not `typing`.
- **Type Hints**: Mandatory for all new code. Use Python 3.13 syntax.
- **Line Length**: 100 characters (enforced by Ruff).

### Coding Practices
- **Error Handling**: Always raise descriptive exceptions. Never return "error dicts" or status codes.
- **Database-First**: Gatherers and tools should index/query ChromaDB directly. Avoid creating intermediate files for data pipelines.
- **Security**: 
    - Use `src/fu7ur3pr00f/utils/security.py` for PII anonymization and SSRF protection.
    - Never log or print API keys/secrets.
    - Keep file-based gatherers scoped to approved local roots: home, the repo workspace, and `/tmp`.
- **Synthesis**: Follow the two-pass synthesis pattern where `AnalysisSynthesisMiddleware` refines specialist outputs.
- **HITL (Human-In-The-Loop)**: Use LangGraph `interrupt()` for destructive or expensive operations (e.g., large-scale web scraping, file deletions).

### Testing Rules
- **Mocking**: Always mock external services (LLMs, HTTP calls, ChromaDB) in unit tests. No real API calls allowed during `pytest`.
- **Fallback Coverage**: Preserve tests for offline keyword routing, local CV parsing, and sandbox-safe cache behavior.
- **Structure**: Tests must mirror the `src` directory structure (e.g., `tests/gatherers/` for `src/fu7ur3pr00f/gatherers/`).
- **Fixtures**: Utilize shared fixtures in `tests/conftest.py`.

## 📂 Key Directory Map

| Path | Purpose |
| :--- | :--- |
| `src/fu7ur3pr00f/agents/` | Orchestrator, Specialists, Blackboard logic, and Tools. |
| `src/fu7ur3pr00f/mcp/` | Model Context Protocol client implementations. |
| `src/fu7ur3pr00f/gatherers/` | Logic for ingesting LinkedIn, GitHub, CVs, etc. |
| `src/fu7ur3pr00f/memory/` | ChromaDB integration, episodic memory, and checkpointers. |
| `src/fu7ur3pr00f/prompts/md/` | Markdown-based prompt templates for all agents. |
| `src/fu7ur3pr00f/chat/` | CLI-based user interface (Typer + Rich + Prompt Toolkit). |
| `scripts/` | Deployment, build, and CI validation scripts. |

---
*This document serves as the primary instructional context for Gemini interactions within this repository.*
