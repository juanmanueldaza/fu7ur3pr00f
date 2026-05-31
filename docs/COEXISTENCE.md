# Coexisting with N3RV

fu7ur3pr00f and [n3rv](https://github.com/juanmanueldaza/n3rv) are separate projects. Neither requires the other. They share an architectural philosophy and integrate through a common runtime (opencode), but operate in different domains with different data.

## Comparison

|                          | n3rv                              | fu7ur3pr00f                     |
|--------------------------|-----------------------------------|---------------------------------|
| **Domain**               | Software engineering infrastructure | Career intelligence infrastructure |
| **Config directory**     | `.n3rv/` (project-local)         | `~/.fu7ur3pr00f/` (user-global)  |
| **ChromaDB scope**       | Project engineering knowledge     | Personal career knowledge       |
| **ChromaDB location**    | `.n3rv/memory/chroma/`           | `~/.fu7ur3pr00f/chroma/`       |
| **MCP servers**          | `n3rv-memory`, `n3rv-hub`         | (none — opencode skills + scripts)  |
| **CLI**                  | `n3rv init`, `n3rv hub start`     | (none — opencode is the interface) |
| **Metaphor**             | Evangelion                        | Future-Proof / Chronological   |
| **Daemon**               | systemd `n3rv-hub.service`        | (none — on-demand scripts only) |
| **Memory types**         | architecture, bugfix, decision, etc. | career_knowledge, career_memories |

## What n3rv owns

- **Engineering memory** — ChromaDB collections for project knowledge. Architecture decisions, bug fixes, patterns, discoveries. Shared across all agents working on the same codebase.
- **A2A task delegation** — Multi-agent coordination via `n3rv-hub`. Routes tasks between agents by skill ID.
- **SDD workflow engine** — 8-phase Spec-Driven Development pipeline with memory artifacts at each phase.
- **Project scaffolding** — `n3rv init` generates agent-native files (AGENTS.md, skills, commands, agents).
- **Adversarial review** — Dual-model judgment day verification against specs.

## What fu7ur3pr00f owns

- **Career knowledge** — ChromaDB collections for professional data. LinkedIn profile, assessments, CVs, portfolio. Personal, not shared across projects.
- **Career workflows** — opencode skills for gathering, analyzing, generating, searching. Career-coach agent for grounded advice.
- **Data gathering pipeline** — LinkedIn ZIP parsing, CliftonStrengths PDF ingestion, CV parsing, portfolio scraping with SSRF protection.
- **CV generation pipeline** — Markdown → sanitized HTML → styled PDF via WeasyPrint with ATS-optimized templates.
- **Job search + tracking** — Market intelligence gathering, application tracking via episodic memory.
- **Career profile management** — Goals, preferences, dealbreakers, target roles. Atomic read-modify-write with thread safety.

## Where they overlap

- **Both use opencode** as the agent runtime. Skills load via the `skill` tool. Commands invoke via slash syntax.
- **Both use ChromaDB** for persistent memory — but separate instances, separate collections, separate storage paths. Zero conflict.
- **Both follow the same code conventions** — Python type hints, pytest, ruff, conventional commits, SDD workflow.
- **Both run MCP servers** — n3rv has `n3rv-memory` and `n3rv-hub`; fu7ur3pr00f currently runs Python scripts directly through opencode.

## How to use them together

A typical workflow with both projects active:

```
# In a project where n3rv is initialized:
opencode
  /sdd-new "refactor auth module"        ← n3rv's SDD workflow (engineering)
  /analyze                                ← fu7ur3pr00f's career analysis (personal)
  /search "staff engineer remote"        ← fu7ur3pr00f's job search (personal)
  /judgment-day                           ← n3rv's adversarial review (engineering)
```

The n3rv hub routes engineering tasks to SDD agents. The career skills operate in the same opencode session using a different ChromaDB instance. They don't interfere because:

1. **Separate storage paths** — `.n3rv/memory/` vs `~/.fu7ur3pr00f/`
2. **Separate collections** — n3rv's `engineering_knowledge` vs fu7ur3pr00f's `career_knowledge` + `career_memories`
3. **Separate skill namespaces** — n3rv's `sdd-*` skills vs fu7ur3pr00f's `career-*` skills

No conflict. No confusion. Two domains, one runtime.
