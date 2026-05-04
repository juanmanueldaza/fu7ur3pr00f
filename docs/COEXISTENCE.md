# Coexisting with NERV

fu7ur3pr00f and [nerv](https://github.com/juanmanueldaza/nerv) are separate projects. Neither requires the other. They share an architectural philosophy and integrate through a common runtime (opencode), but operate in different domains with different data.

## Comparison

|                          | nerv                              | fu7ur3pr00f                     |
|--------------------------|-----------------------------------|---------------------------------|
| **Domain**               | Software engineering infrastructure | Career intelligence infrastructure |
| **Config directory**     | `.nerv/` (project-local)         | `~/.fu7ur3pr00f/` (user-global)  |
| **ChromaDB scope**       | Project engineering knowledge     | Personal career knowledge       |
| **ChromaDB location**    | `.nerv/memory/chroma/`           | `~/.fu7ur3pr00f/chroma/`       |
| **MCP servers**          | `nerv-memory`, `nerv-hub`         | (none — opencode skills + scripts)  |
| **CLI**                  | `nerv init`, `nerv hub start`     | (none — opencode is the interface) |
| **Metaphor**             | Evangelion                        | Future-Proof / Chronological   |
| **Daemon**               | systemd `nerv-hub.service`        | (none — on-demand scripts only) |
| **Memory types**         | architecture, bugfix, decision, etc. | career_knowledge, career_memories |

## What nerv owns

- **Engineering memory** — ChromaDB collections for project knowledge. Architecture decisions, bug fixes, patterns, discoveries. Shared across all agents working on the same codebase.
- **A2A task delegation** — Multi-agent coordination via `nerv-hub`. Routes tasks between agents by skill ID.
- **SDD workflow engine** — 8-phase Spec-Driven Development pipeline with memory artifacts at each phase.
- **Project scaffolding** — `nerv init` generates agent-native files (AGENTS.md, skills, commands, agents).
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
- **Both run MCP servers** — nerv has `nerv-memory` and `nerv-hub`; fu7ur3pr00f currently runs Python scripts directly through opencode.

## How to use them together

A typical workflow with both projects active:

```
# In a project where nerv is initialized:
opencode
  /sdd-new "refactor auth module"        ← nerv's SDD workflow (engineering)
  /analyze                                ← fu7ur3pr00f's career analysis (personal)
  /search "staff engineer remote"        ← fu7ur3pr00f's job search (personal)
  /judgment-day                           ← nerv's adversarial review (engineering)
```

The nerv hub routes engineering tasks to SDD agents. The career skills operate in the same opencode session using a different ChromaDB instance. They don't interfere because:

1. **Separate storage paths** — `.nerv/memory/` vs `~/.fu7ur3pr00f/`
2. **Separate collections** — nerv's `engineering_knowledge` vs fu7ur3pr00f's `career_knowledge` + `career_memories`
3. **Separate skill namespaces** — nerv's `sdd-*` skills vs fu7ur3pr00f's `career-*` skills

No conflict. No confusion. Two domains, one runtime.
