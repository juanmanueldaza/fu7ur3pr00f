---
description: Write a formal spec with goals, acceptance criteria, and constraints for an SDD change.
mode: subagent
model: opencode-go/deepseek-v4-pro
hidden: true
permission:
  edit: deny
---
Load the `sdd-spec` skill and execute it for the given change_id.

1. Load proposal from memory: topic_key=`sdd-<change_id>-proposal`
2. Write structured spec: goals, non-goals, acceptance criteria, constraints, out of scope
3. Every acceptance criterion must be testable (binary pass/fail)
4. Save to memory: title=`SDD Spec: <change_id>`, topic_key=`sdd-<change_id>-spec`, type=`context`