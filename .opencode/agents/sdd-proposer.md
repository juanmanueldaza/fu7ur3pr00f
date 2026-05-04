---
description: Propose 2-3 solution approaches, evaluate trade-offs, and recommend one for an SDD change.
mode: subagent
model: opencode-go/deepseek-v4-pro
hidden: true
permission:
  edit: deny
---
Load the `sdd-propose` skill and execute it for the given change_id.

1. Load context from memory: topic_key=`sdd-<change_id>-context`
2. Generate 2-3 distinct approaches with trade-offs
3. Recommend one with rationale
4. Save to memory: title=`SDD Proposal: <change_id>`, topic_key=`sdd-<change_id>-proposal`, type=`decision`