# fu7ur3pr00f — The Future-Proof Harness

> "The best way to predict the future is to prepare for it."

Invisible infrastructure that harnesses AI agents for career intelligence.

## Concept Map

| Concept | Subsystem | What it does |
|---------|-----------|-------------|
| **The Chronograph** | Career Timeline | Track your career across time — positions, skills, achievements. Every role, every project, every certification in one searchable history. |
| **The Repository** | ChromaDB Knowledge Store | Persistent career memory. LinkedIn exports, CliftonStrengths assessments, CVs, portfolio data — indexed as vector embeddings for semantic recall. |
| **The Observatory** | Market Intelligence | Scan the horizon. Job board searches, application tracking, market trend awareness. See what's coming. |
| **The Forge** | CV Generation | Shape raw career data into professional artifacts. Markdown-to-PDF pipeline with ATS-optimized templates. |
| **The Compass** | Skills + Gap Analysis | Compare where you are against where you want to be. Structured gap reports, alignment scores, market fit analysis. Direction, not destination. |
| **The Profile** | Career Identity | Your career DNA — goals, preferences, dealbreakers, target roles. The pilot's seat. Persisted as `~/.fu7ur3pr00f/profile.yaml`. |

## Why This Metaphor

**"Future-proof"** is inherently temporal. Career intelligence is about understanding your past (Chronograph), knowing your present (Profile), and preparing for your future (Observatory, Compass, Forge). Each subsystem answers a question about time:

- *Where have I been?* — The Chronograph
- *What do I know?* — The Repository
- *What's out there?* — The Observatory
- *How do I present myself?* — The Forge
- *Where am I going?* — The Compass
- *Who am I?* — The Profile

No anime universes. No borrowed mythologies. The name provides the metaphor.

## Relationship with NERV

[nerv](https://github.com/juanmanueldaza/nerv) is **invisible infrastructure for AI agents doing software engineering**. fu7ur3pr00f is **invisible infrastructure for AI agents doing career intelligence**. Same architecture philosophy — MCP servers, opencode-native skills, ChromaDB memory, SDD workflow. Different domains. Complementary, not dependent.

See [docs/COEXISTENCE.md](docs/COEXISTENCE.md) for the full breakdown.

## Architecture

```
opencode CLI
    │
    ▼
.opencode/skills/career-*/SKILL.md     ← AI instructions (The Compass, The Forge, The Observatory)
.opencode/commands/*.md                 ← User slash commands
    │
    ▼
scripts/gather/*.py                     ← Data ingestion (The Chronograph, The Repository)
scripts/generate/*.py                   ← PDF rendering (The Forge)
    │
    ▼
src/fu7ur3pr00f/
  ├── gatherers/    ← LinkedIn, CliftonStrengths, CV, portfolio parsers
  ├── generators/   ← Markdown → PDF (WeasyPrint)
  ├── memory/       ← ChromaDB knowledge + episodic stores (The Repository)
  └── utils/        ← Security, data loading
    │
    ▼
ChromaDB (~/.fu7ur3pr00f/)              ← Vector search, semantic recall
```

## Future Horizons

Capabilities on the roadmap — infrastructure that doesn't exist yet but follows from the same harness engineering approach:

- **The Oracle** — Career trajectory simulation. "If I take this role, where could I be in 3 years?"
- **The Network** — Professional relationship intelligence. Map and understand your network topology.
- **The Simulator** — Interview preparation harness. Mock technical and behavioral rounds with feedback.
- **The Negotiator** — Compensation intelligence. Market salary data, equity benchmarks, offer comparison.

---

Powered by [opencode](https://opencode.ai). Pattern-aligned with [nerv](https://github.com/juanmanueldaza/nerv).
