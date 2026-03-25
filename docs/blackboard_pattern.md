# Blackboard Pattern - Multi-Specialist Collaboration

## Overview

The **blackboard pattern** enables multiple specialists (AI agents) to collaborate iteratively on complex problems by sharing a common state (the "blackboard") rather than operating independently.

### Traditional Multi-Agent vs Blackboard Pattern

**Before (Independent Multi-Agents):**
```
User: "5-year prediction"
  ↓
Coach: "Target Staff Engineer role"
Learning: "Learn Python ML" (doesn't know this was Coach's suggestion)
Code: "Build portfolio" (doesn't know learning timeline)
Jobs: "Found freelance opportunity" (no context from others)
Founder: "Launch SaaS" (ignores freelance as interim step)
  ↓
User gets 5 separate reports with gaps and overlap
```

**Now (Blackboard Pattern):**
```
User: "5-year prediction"
  ↓
Iteration 1:
  Coach → "Staff Engineer role, needs ML + leadership"
  ↓ blackboard updated
Iteration 2:
  Learning → reads Coach's gaps → "ML fundamentals + leadership coaching"
  ↓ blackboard updated
Iteration 3:
  Code → reads Learning timeline → "Portfolio projects for ML and team lead"
  ↓ blackboard updated
Iteration 4:
  Jobs → reads Code strategy → "Freelance funds learning timeline"
  ↓ blackboard updated
Iteration 5:
  Founder → reads all findings → "Integrated 5-year roadmap"
  ↓
User gets ONE integrated advice with clear reasoning chain
```

## Architecture

### The Blackboard (Shared State)

`CareerBlackboard` is a TypedDict containing:

```python
{
    "query": "5-year prediction",
    "user_profile": {...},
    
    "findings": {
        "coach": {"gaps": [...], "target_role": "Staff Engineer", "confidence": 0.85},
        "learning": {"skills": [...], "timeline": "6-12 months", "confidence": 0.80},
        "code": {"portfolio": [...], "confidence": 0.82},
        "jobs": {"opportunities": [...], "confidence": 0.85},
        "founder": {"stages": [...], "confidence": 0.75},
    },
    
    "change_log": [
        {"iteration": 0, "specialist": "coach", "keys_modified": ["gaps", "target_role"]},
        {"iteration": 1, "specialist": "learning", "keys_modified": ["skills", "timeline"]},
        ...
    ],
    
    "synthesis": {...},  # Final integrated advice
    "errors": [],
    "iteration": 5,
    "max_iterations": 5,
}
```

### Three Key Components

#### 1. **CareerBlackboard** (`blackboard.py`)
- Defines the shared state structure
- Provides helper functions:
  - `make_initial_blackboard()` - Create initial state
  - `record_specialist_contribution()` - Record findings
  - `get_specialist_finding()` - Retrieve a specialist's findings
  - `get_previous_findings()` - Read what other specialists found

#### 2. **BlackboardScheduler** (`scheduler.py`)
- Decides which specialist contributes next
- Supports multiple strategies:
  - **linear**: Each specialist once in fixed order
  - **linear_iterative**: Specialists run in loops (default)
  - **conditional**: Only activate specialists matching query keywords
  - **smart**: Route based on blackboard state (dependencies)

#### 3. **BlackboardExecutor** (`executor.py`)
- Orchestrates the execution:
  1. Initialize blackboard with user query/profile
  2. Loop: scheduler picks next specialist → specialist reads blackboard → contributes findings
  3. Repeat until max iterations reached
  4. Synthesize final advice from all findings

## Usage

### Basic Usage (Recommended)

```python
from fu7ur3pr00f.agents.specialists.orchestrator import get_orchestrator

# Get orchestrator and create executor
orchestrator = get_orchestrator()
executor = orchestrator.get_blackboard_executor()

# Execute multi-specialist analysis
blackboard = executor.execute(
    query="5-year career prediction",
    user_profile={
        "role": "Senior Engineer",
        "skills": ["Python", "Go"],
        "goals": ["Staff role"],
    },
)

# Access results
print(blackboard["findings"])     # All specialist findings
print(blackboard["synthesis"])    # Integrated advice
print(blackboard["change_log"])   # Audit trail
```

### With Progress Callbacks

```python
def on_specialist_start(name: str):
    print(f"[{name.upper()}] analyzing...")

def on_specialist_complete(name: str, findings: dict):
    print(f"[{name.upper()}] found {len(findings)} items")

blackboard = executor.execute(
    query="5-year prediction",
    user_profile={...},
    on_specialist_start=on_specialist_start,
    on_specialist_complete=on_specialist_complete,
)
```

### Custom Scheduler

```python
from fu7ur3pr00f.agents.blackboard.scheduler import BlackboardScheduler

# 3 iterations of smart scheduling
scheduler = BlackboardScheduler(
    strategy="smart",
    max_iterations=3,
)

executor = orchestrator.get_blackboard_executor(scheduler=scheduler)
blackboard = executor.execute(...)
```

## Specialist Contribution

### The Old Way (Stream)

```python
# Specialist streams directly to user
agent = orchestrator.get_compiled_agent("coach")
agent.stream(
    {"messages": [HumanMessage(query)]},
    config=config,
)
```

### The New Way (Contribute)

```python
# Specialist reads blackboard, writes findings, returns them
finding = specialist.contribute(blackboard)

# finding = {
#     "gaps": ["ML", "leadership"],
#     "target_role": "Staff Engineer",
#     "confidence": 0.85,
#     "reasoning": "..."
# }
```

The key difference: **specialists read what other specialists found and focus on gaps/next steps instead of repeating analysis**.

## Specialist Collaboration Example

**Coach (Iteration 1):**
- Reads: User profile
- Analyzes: Career trajectory, gaps
- Writes: `{"gaps": ["ML", "leadership"], "target_role": "Staff Engineer"}`

**Learning (Iteration 2):**
- Reads: Coach's gaps
- Analyzes: How to fill those specific gaps
- Writes: `{"skills": ["ML fundamentals", "leadership coaching"], "timeline": "6-12 months"}`

**Code (Iteration 3):**
- Reads: Learning's skills/timeline
- Analyzes: Portfolio projects that teach those skills
- Writes: `{"portfolio_items": [{"name": "ML chatbot", "timeline": "3 months"}]}`

**Jobs (Iteration 4):**
- Reads: Code's timeline, Coach's target role
- Analyzes: Opportunities matching that timeline
- Writes: `{"opportunities": ["Freelance AI", "Contract ML roles"]}`

**Founder (Iteration 5):**
- Reads: All previous findings
- Synthesizes: 5-year roadmap
- Writes: `{"stages": [{"year": "0-1", "focus": "Freelance + ML"}, ...]}`

## Auto-Detection (When to Use Blackboard)

The orchestrator auto-detects comprehensive queries:

```python
if orchestrator.should_use_blackboard(query):
    # Use blackboard pattern
    executor = orchestrator.get_blackboard_executor()
    blackboard = executor.execute(...)
else:
    # Use traditional streaming
    route = orchestrator.route(query)
    agent = orchestrator.get_compiled_agent(route)
    agent.stream(...)
```

**Triggers blackboard for:**
- "5-year prediction"
- "Complete career portrait"
- "Overall strategy"
- "Comprehensive advice"
- "Make all decisions"

**Uses traditional streaming for:**
- "How do I get promoted?"
- "What skills should I learn?"
- "Freelance vs employment?"

## Architecture Diagram

```
┌─────────────────────────────────────┐
│         Chat Interface              │
│   (user types query)                │
└────────────────┬────────────────────┘
                 │
        ┌────────▼───────────┐
        │ OrchestratorAgent  │
        │ - should_use_...() │
        │ - get_executor()   │
        └────────┬───────────┘
                 │
      ┌──────────▼──────────────────┐
      │  BlackboardExecutor         │
      │  .execute()                 │
      └──────────┬──────────────────┘
                 │
    ┌────────────▼─────────────────┐
    │   BlackboardScheduler        │
    │   .get_next_specialist()     │
    └────────────┬────────────────┘
                 │
        ┌────────▼───────────┐
        │ While next exists:  │
        │ 1. Coach            │
        │ 2. Learning         │
        │ 3. Code             │
        │ 4. Jobs             │
        │ 5. Founder          │
        │ [Loop]              │
        └────────┬───────────┘
                 │
    ┌────────────▼─────────────────┐
    │ Specialist.contribute()       │
    │ - Read blackboard             │
    │ - Analyze in context          │
    │ - Write findings              │
    │ - Return structured findings  │
    └────────────┬────────────────┘
                 │
    ┌────────────▼─────────────────┐
    │   CareerBlackboard (State)    │
    │   - Record findings           │
    │   - Log changes               │
    │   - Keep audit trail          │
    └────────────┬────────────────┘
                 │
        ┌────────▼───────────┐
        │  Synthesis Engine  │
        │  Integrate findings│
        │  Return final plan │
        └────────┬───────────┘
                 │
        ┌────────▼───────────────┐
        │  Display to User        │
        │  - Integrated advice    │
        │  - Audit trail          │
        │  - Show reasoning       │
        └────────────────────────┘
```

## Key Benefits

### 1. **Integrated Advice**
Instead of 5 separate reports, users get one cohesive plan where specialists build on each other's insights.

### 2. **No Redundancy**
Each specialist focuses on their domain without repeating what others already analyzed.

### 3. **Iterative Refinement**
Specialists can run multiple times, refining findings based on what they learn from each other.

### 4. **Transparent Reasoning**
The change log shows exactly how the conclusion was reached: "COACH identified gaps → LEARNING addressed them → CODE validated with projects → JOBS found funding → FOUNDER staged 5-year plan"

### 5. **Confidence Tracking**
Each finding has a confidence score. Higher-confidence findings guide lower-confidence ones.

## Extending the Pattern

### Custom Specialist Contribution

Override `contribute()` in a specialist class:

```python
class CoachAgent(BaseAgent):
    def contribute(self, blackboard: CareerBlackboard) -> SpecialistFinding:
        """Coach specializes in career trajectory analysis."""
        
        # Read blackboard context
        query = blackboard["query"]
        user_profile = blackboard["user_profile"]
        previous = get_previous_findings(blackboard, "coach")
        
        # Build context-aware prompt
        context_msg = "Previous specialists found:\n"
        for name, finding in previous.items():
            context_msg += f"- {name}: {finding.get('key_insight')}\n"
        
        # Call LLM with context
        response = self._call_llm(f"{query}\n{context_msg}")
        
        # Return structured findings
        return {
            "gaps": response["gaps"],
            "target_role": response["target_role"],
            "timeline": response["timeline"],
            "confidence": response["confidence"],
        }
```

### Custom Scheduler Strategy

```python
class SmartScheduler(BlackboardScheduler):
    def __init__(self):
        super().__init__(strategy="smart")
    
    def get_next_specialist(self, blackboard, current):
        # Custom logic: check blackboard state to decide next
        findings = blackboard["findings"]
        
        if current == "coach" and findings["coach"].get("learning_needed"):
            return "learning"
        elif current == "learning" and findings["learning"].get("projects"):
            return "code"
        # ... etc
        
        return None
```

## Testing

Run blackboard tests:

```bash
PYTHONPATH=src pytest tests/agents/blackboard/test_blackboard.py -v
```

Key test areas:
- Blackboard creation and state management
- Specialist contribution recording
- Scheduler ordering (linear, iterative, smart)
- Executor orchestration
- Integration between specialists

## Performance

- **No extra cost**: Specialists are cached (compiled LangGraph agents)
- **Sequential execution**: Specialists run one at a time (not parallel) for iterative refinement
- **Typical time**: 3-5 iterations × 5 specialists ≈ 15-25 LLM calls

## Next Steps

1. **Implement specialized `contribute()` methods** in each specialist to optimize blackboard collaboration
2. **Add confidence-based conflict resolution** when specialists disagree
3. **Implement backtracking** - if a finding has low confidence, re-run that specialist
4. **Add `/show-reasoning` command** to display the full audit trail to users
5. **Optimize scheduler** - use reinforcement learning to find best specialist order

## Troubleshooting

### Specialists Not Contributing
Check that `should_use_blackboard()` returns `True` for your query, and that `get_blackboard_executor()` is called.

### Missing Findings
Verify specialists are actually returning structured findings (not None). Check log for errors.

### Long Execution Time
Reduce `max_iterations` in the scheduler, or switch to `linear` strategy (one pass only).

### Conflicting Findings
Check confidence scores in the change log. Higher confidence findings should guide synthesis.

## References

- **HEARSAY-II** (1976): Original blackboard pattern for speech recognition
- **CrewAI**: Modern multi-agent framework with task context-passing
- **AutoGen**: Microsoft's group chat approach (conversation history as blackboard)
- **LangGraph**: Built-in state management for agent coordination

## Files

```
src/fu7ur3pr00f/agents/blackboard/
├── __init__.py          # Public API
├── blackboard.py        # State definition & helpers
├── scheduler.py         # Scheduling logic
└── executor.py          # Orchestration engine

src/fu7ur3pr00f/agents/specialists/
├── base.py             # Updated: added contribute() method
└── orchestrator.py     # Updated: added blackboard methods

tests/agents/blackboard/
└── test_blackboard.py  # Unit & integration tests

examples/
└── blackboard_example.py # End-to-end example
```
