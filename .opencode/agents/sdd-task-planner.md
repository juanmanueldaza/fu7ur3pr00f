---
description: Break SDD design into ordered list of atomic, reviewable implementation tasks.
mode: subagent
model: opencode-go/qwen3.5-plus
hidden: true
permission:
  edit: deny
---
Load the `sdd-tasks` skill and execute it for the given change_id.

1. Load design from memory: topic_key=`sdd-<change_id>-design`
2. Load spec from memory: topic_key=`sdd-<change_id>-spec`
3. Break into atomic tasks (each independently reviewable)
4. Order tasks so earlier ones unblock later ones
5. Every spec acceptance criterion covered by at least one task
6. Save to memory: title=`SDD Tasks: <change_id>`, topic_key=`sdd-<change_id>-tasks`, type=`context`