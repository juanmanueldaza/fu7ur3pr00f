# Archive Report: suggest-next-fail-fast

## Change Archived

**Change**: `suggest-next-fail-fast`  
**Archived to**: `openspec/changes/archive/2026-04-12-suggest-next-fail-fast/`

### Specs Synced

| Domain | Action | Details |
|--------|--------|---------|
| `outer-conversation-graph` | Updated | Added fail-soft suggestion-generation requirement: on LLM failure, `suggest_next_node` returns `[]`, logs the warning, and does not fabricate heuristic suggestions. |

### Archive Contents

- `proposal.md` ✅
- `spec.md` ✅
- `design.md` ✅
- `tasks.md` ✅
- `verify-report.md` ✅

### Source of Truth Updated

- `openspec/specs/outer-conversation-graph/spec.md`

### Notes

- This report was added during archive normalization to make the older archive
  conform to the explicit per-change archive-report convention.
- Folder name normalized from legacy path:
  `openspec/changes/archive/suggest-next-fail-fast/`

### SDD Cycle Complete

The change has been fully planned, implemented, verified, archived, and now has
an explicit archive report.
