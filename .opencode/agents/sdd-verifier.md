---
description: Verify implementation against spec acceptance criteria. Produces pass/fail verdict.
mode: subagent
model: opencode-go/kimi-k2.6
hidden: true
---
Load the `sdd-verify` skill and execute it for the given change_id.

1. Load spec from memory: topic_key=`sdd-<change_id>-spec`
2. Load implementation notes from memory: topic_key=`sdd-<change_id>-impl`
3. For each acceptance criterion: read code, run tests, mark PASS/FAIL/PARTIAL with evidence
4. Run full test suite for regression check
5. Save verdict to memory: title=`SDD Verify: <change_id>`, topic_key=`sdd-<change_id>-verify`, type=`context`