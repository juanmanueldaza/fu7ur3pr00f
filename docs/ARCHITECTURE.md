# Architecture

fu7ur3pr00f is an **opencode-native workspace**: skills define workflows, commands invoke them, Python scripts do the heavy lifting, ChromaDB stores the results.

## System Overview

```
┌──────────────────────────────────────────────────────────┐
│                    opencode Agent (AI)                    │
│  Uses skills + commands + scripts to operate on career data  │
└──┬────────────────┬───────────────┬──────────────────────┘
   │                │               │
   │ skills         │ commands      │ scripts
   ▼                ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────────────────┐
│ Skills   │  │ Commands │  │ Python Entry Points   │
│ career-* │  │ /gather  │  │ scripts/gather/*.py   │
│ SKILL.md │  │ /analyze │  │ scripts/generate/*.py │
└────┬─────┘  │ /generate│  └──────────┬───────────┘
     │        │ /search  │             │
     │        │ /profile │             │
     │        └──────────┘             │
     │                                 │
     ▼                                 ▼
┌──────────────────────────────────────────────────────────┐
│                   src/fu7ur3pr00f/                       │
│                                                          │
│  gatherers/          generators/         memory/         │
│  ├ linkedin.py       └ cv_generator.py   ├ chromadb_store.py │
│  ├ cliftonstrengths.py                   ├ knowledge.py   │
│  ├ cv.py                                 ├ episodic.py   │
│  └ portfolio/                            ├ profile.py    │
│                                          ├ embeddings.py │
│  utils/              prompts/            └ chunker.py    │
│  ├ security.py       ├ loader.py                         │
│  ├ data_loader.py    └ builders.py                       │
│  ├ logging.py        prompts/md/ (28 templates)          │
│  └ console.py                                            │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              ChromaDB (~/.fu7ur3pr00f/)                  │
│                                                          │
│  Collection: "career_knowledge"   ← factual career data  │
│  Collection: "career_memories"    ← episodic decisions   │
│  File: ~/.fu7ur3pr00f/profile.yaml ← career identity     │
└──────────────────────────────────────────────────────────┘
```

## Components

### Skills (`.opencode/skills/career-*/SKILL.md`)

Six career-domain skills loaded on demand by opencode:

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `career-gather` | `/gather` command, "collect my data" | Orchestrate data collection — LinkedIn, CliftonStrengths, CV, portfolio |
| `career-analyze` | `/analyze` command, "analyze my skills" | Skill gap analysis, career alignment, market fit |
| `career-cv` | `/generate` command, "create my CV" | ATS-optimized CV generation (markdown + PDF) |
| `career-search` | `/search` command, "find jobs" | Job board search, application tracking |
| `career-profile` | `/profile` command, "update my profile" | View/edit career identity, goals, preferences |
| `career-coach` | "give me career advice" | Grounded career guidance using accumulated data |

### Commands (`.opencode/commands/*.md`)

User-invocable slash commands displayed in the opencode TUI:

| Command | Agent | Skill | Purpose |
|---------|-------|-------|---------|
| `/gather` | build | career-gather | Collect professional data |
| `/analyze` | build | career-analyze | Skill gap analysis |
| `/generate` | build | career-cv | Generate ATS-optimized CV |
| `/search` | build | career-search | Job search + tracking |
| `/profile` | build | career-profile | View/edit career profile |

### Scripts

Standalone Python entry points for data operations:

| Script | Input | Output |
|--------|-------|--------|
| `gather_linkedin.py` | LinkedIn ZIP export path | Sections → ChromaDB |
| `gather_portfolio.py` | Optional portfolio URL | Sections → ChromaDB |
| `gather_assessment.py` | Optional PDF directory | Sections → ChromaDB |
| `gather_cv.py` | CV file path (.pdf/.md/.txt) | Sections → ChromaDB |
| `render_cv.py` | Markdown CV path | Rendered PDF |

Each script follows the same pattern: instantiate gatherer → `gather(input)` → `knowledge_store.index_sections(source, sections)` → safe-swap old chunks.

### Gatherers (`src/fu7ur3pr00f/gatherers/`)

Domain-specific data parsers producing `Section(name, content)` tuples:

- **LinkedInGatherer** (`linkedin.py:676L`) — Parses LinkedIn ZIP exports: 19 CSVs across 3 tiers (core, intelligence, network). Security: ZIP bomb detection (500MB limit), path traversal checks, email anonymization.
- **CliftonStrengthsGatherer** (`cliftonstrengths.py:651L`) — Parses Gallup PDFs via `pdftotext`. Detects report type from filename indicators. Maps 34 strengths to 4 domains (Executing, Influencing, Relationship Building, Strategic Thinking). Outputs 10+ labeled sections.
- **CVGatherer** (`cv.py:266L`) — Parses CV/resume files (.pdf/.md/.txt). PDF via `pdftotext -layout`. Regex-based section heading detection. Falls back to raw text if no structured sections found.
- **PortfolioGatherer** (`portfolio/`) — Four-component pipeline: SSRF-protected HTTP fetcher → BeautifulSoup HTML extraction → JSON-LD/data-attribute JS extraction → Markdown section generation. Security: DNS pinning, private/CGNAT IP blocking, per-hop redirect validation.

### Generators (`src/fu7ur3pr00f/generators/`)

- **cv_generator.py** — Markdown CV → sanitized HTML → styled A4 PDF via WeasyPrint. Georgia font, goldenrod accents, uppercase section headers. Blocks external resource fetching in PDF for SSRF safety.

### Memory Subsystem (`src/fu7ur3pr00f/memory/`)

| Module | Class | Purpose |
|--------|-------|---------|
| `chromadb_store.py` | `ChromaDBStore` | Base class: PersistentClient, collection management, thread-safe batch insert/query/delete |
| `knowledge.py` | `CareerKnowledgeStore` | Collection `"career_knowledge"` — facts indexed by source (LINKEDIN, PORTFOLIO, ASSESSMENT, CV) with section-level metadata |
| `episodic.py` | `EpisodicStore` | Collection `"career_memories"` — decisions and job applications with temporal context |
| `profile.py` | `UserProfile` | `~/.fu7ur3pr00f/profile.yaml` — atomic read-modify-write with threading lock |
| `embeddings.py` | `CachedEmbeddingFunction` | Provider chain: explicit → Azure OpenAI → OpenAI → proxy → Ollama → ChromaDB default. LRU cache (max 1000 entries) |
| `chunker.py` | `MarkdownChunker` | Splits sections into token-bounded chunks (max 500 tokens, ~1.3 tokens/word) at paragraph boundaries |

## Memory Schema

```
career_knowledge:
  id: UUID
  document: chunk text
  metadata:
    source: "linkedin" | "portfolio" | "assessment" | "cv"
    section: "Experience" | "Skills" | "Education" | ...
    chunk_index: 0, 1, 2, ...

career_memories:
  id: UUID
  document: memory text
  metadata:
    memory_type: "decision" | "application"
    context: "..."
    timestamp: ISO8601
    company: "..." (applications only)
    role: "..." (applications only)
    status: "..." (applications only)
```

## Data Flows

### Gathering Data

```
User → /gather → career-gather skill → gather script → Gatherer class → list[Section]
  → CareerKnowledgeStore.index_sections() → sections chunked → batch-indexed (100/batch)
  → safe-swap: clear_source() then insert new chunks
```

### Generating a CV

```
User → /generate → career-cv skill → load_career_data_for_cv() from ChromaDB
  → Position details, Skills, Experience, Education combined → LLM generates markdown CV
  → save_cv_markdown() → render_cv_pdf() via WeasyPrint
```

### Analyzing Skills

```
User → /analyze → career-analyze skill → load_career_data() from ChromaDB (filtered: no Connections, Messages, Job Apps)
  → Profile loaded from ~/.fu7ur3pr00f/profile.yaml → target_roles + skills
  → LLM compares profile against target → structured gap report
```

### Searching Market

```
User → /search → career-search skill → job board queries → structured listings
  → Application tracked via EpisodicStore.remember_application()
  → Past applications recallable via EpisodicStore.recall()
```

## Security Architecture

See [SECURITY.md](SECURITY.md) for the full trust model and attack surface analysis. Key protections:

- **File I/O**: `secure_open()` with `os.open()` + `os.fchmod()` (0o600), no TOCTOU window
- **PII**: 12 regex patterns in `anonymize_career_data()`, email anonymization
- **Prompt injection**: XML boundary escaping, API key redaction
- **SSRF**: DNS pinning, private/CGNAT IP blocking, per-hop redirect validation

## Concept Map

See [FUTUREPROOF.md](../FUTUREPROOF.md) for the full future-proof concept map — where each subsystem maps to a temporal career concept.
