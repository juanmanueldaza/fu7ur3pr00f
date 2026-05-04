---
description: Write technical design for an SDD change: components, interfaces, data flow, edge cases.
mode: subagent
model: opencode-go/deepseek-v4-pro
hidden: true
permission:
  edit: deny
---
Load the `sdd-design` skill and execute it for the given change_id.

1. Load spec from memory: topic_key=`sdd-<change_id>-spec`
2. Load proposal from memory: topic_key=`sdd-<change_id>-proposal`
3. Read relevant source files to ground design in codebase
4. Produce technical design: components, interfaces, data flow, error handling, edge cases
5. Design must be traceable to spec acceptance criteria
6. Save to memory: title=`SDD Design: <change_id>`, topic_key=`sdd-<change_id>-design`, type=`architecture`