# Comprehensive Code Audit Prompt: DRY, SOLID, KISS, YAGNI

## Mission

You are a senior software architect conducting an exhaustive code quality audit of the **fu7ur3pr00f** career intelligence agent codebase. Your goal is to identify every violation of DRY, SOLID, KISS, and YAGNI principles with surgical precision.

---

## Context

**Project**: fu7ur3pr00f — AI-powered career intelligence agent  
**Stack**: Python 3.13, LangChain/LangGraph, ChromaDB, MCP, Typer+Rich CLI  
**Architecture**: Single agent with 41 tools OR multi-agent blackboard pattern with 5 specialists  
**Key Patterns**: Dependency inversion, database-first, prompt-driven, two-pass synthesis, HITL confirmation

---

## Audit Framework

### Phase 1: DRY (Don't Repeat Yourself)

**Search for:**

1. **Duplicate Logic Across Files**
   - Similar functions in different modules that could be consolidated
   - Repeated validation, parsing, or transformation logic
   - Copy-pasted error handling patterns
   - Duplicated utility functions across `utils/`, `gatherers/`, `mcp/`

2. **Repeated Code in Specialists**
   - Check `agents/specialists/{coach,jobs,learning,code,founder}.py` for similar implementations
   - Look for repeated tool patterns that could use `toolkits.py` more effectively
   - Identify if specialists share initialization or setup logic

3. **MCP Client Duplication**
   - All 12 MCP clients extend `MCPClient` ABC — check for repeated implementation details
   - Look for similar HTTP patterns that could be in `mcp/base.py`
   - Check if error handling is consistent or duplicated

4. **Gatherer Patterns**
   - Compare `gatherers/linkedin.py`, `cv.py`, `cliftonstrengths.py` for repeated parsing logic
   - Check `gatherers/market/*.py` for repeated caching/fetch patterns beyond `base.py`
   - Look for repeated ChromaDB indexing logic

5. **Memory Subsystem**
   - Compare `memory/knowledge.py` vs `memory/episodic.py` — should they share more base logic?
   - Check if chunking/embedding logic is duplicated elsewhere

6. **Tool Implementations**
   - Scan `agents/tools/*.py` files for similar tool patterns
   - Look for repeated validation, formatting, or error handling

7. **Prompt Repetition**
   - Check `prompts/md/*.md` files for repeated instructions or context
   - Look for prompts that could inherit from templates via `builders.py`

8. **Configuration Access**
   - Check if `settings` singleton access is repeated vs. could be injected
   - Look for repeated path construction logic

**Questions to Ask:**
- "If I change this logic, how many other places need the same change?"
- "Is this pattern implemented 3+ times with minor variations?"
- "Could this be a mixin, base class method, or utility function?"

---

### Phase 2: SOLID Principles

#### S — Single Responsibility Principle

**Search for:**

1. **God Classes/Functions**
   - Classes with 10+ public methods doing unrelated things
   - Functions with 50+ lines handling multiple concerns
   - Tools that both fetch AND process AND format data

2. **Mixed Concerns**
   - Business logic mixed with presentation logic
   - Data access mixed with validation logic
   - Configuration logic mixed with business logic

3. **Specific Files to Scrutinize:**
   - `agents/specialists/orchestrator.py` — is it doing too much?
   - `agents/blackboard/executor.py` — single responsibility or coordinator?
   - `chat/client.py` — UI logic vs. business logic separation
   - `cli.py` — command routing vs. implementation

**Questions to Ask:**
- "Does this class/function have more than one reason to change?"
- "Can I clearly state what this does in one sentence?"
- "If I remove this method, does the class lose its core purpose?"

---

#### O — Open/Closed Principle

**Search for:**

1. **Closed for Extension**
   - Classes marked `final` that should be extensible
   - Switch statements on types that should use polymorphism
   - Hardcoded conditionals that should be strategy patterns

2. **Specific Checks:**
   - `agents/specialists/routing.py` — can new specialists be added without modification?
   - `mcp/factory.py` — does adding a client require modifying existing code?
   - `tools/__init__.py` — is tool registration extensible?
   - `llm/model_selection.py` — can new providers be added easily?

3. **Inheritance vs. Composition**
   - Deep inheritance trees that are hard to extend
   - Base classes with too many hooks vs. composition-based extension

**Questions to Ask:**
- "To add feature X, do I need to modify existing tested code?"
- "Is extension done via inheritance/composition rather than editing?"
- "Are there switch/if-elif chains on types or enums?"

---

#### L — Liskov Substitution Principle

**Search for:**

1. **Subclass Surprises**
   - Subclasses that override methods with incompatible behavior
   - Subclasses that raise unexpected exceptions
   - Subclasses that change return type semantics

2. **Specific Checks:**
   - All `MCPClient` subclasses — do they honor the base contract?
   - All `BaseAgent` subclasses — consistent behavior?
   - All `MarketGatherer` subclasses — same caching semantics?
   - Check `memory/*.py` stores — interchangeable?

3. **Precondition/Postcondition Violations**
   - Subclasses with stricter input requirements
   - Subclasses with weaker output guarantees

**Questions to Ask:**
- "Can I replace the base class with this subclass without breaking code?"
- "Does this subclass throw exceptions the base class doesn't?"
- "Does this subclass have additional required setup?"

---

#### I — Interface Segregation Principle

**Search for:**

1. **Fat Interfaces**
   - ABCs with 10+ methods that subclasses don't all use
   - Protocols with unrelated method groups
   - Tools that expose methods only some consumers need

2. **Specific Checks:**
   - `mcp/base.py` — does `MCPClient` ABC have unused methods for some clients?
   - `agents/specialists/base.py` — do all specialists use all base methods?
   - `memory/chromadb_store.py` — are all methods needed by both knowledge and episodic?

3. **Unused Method Patterns**
   - Methods that raise `NotImplementedError`
   - Methods with `pass` in multiple subclasses

**Questions to Ask:**
- "Do clients need to implement methods they don't use?"
- "Are there `NotImplementedError` or empty override methods?"
- "Could this interface be split into focused protocols?"

---

#### D — Dependency Inversion Principle

**Search for:**

1. **Concrete Dependencies**
   - Direct instantiation of external services (ChromaDB, LLMs, HTTP clients)
   - Hardcoded imports of concrete classes instead of abstractions
   - Modules that import specific implementations vs. protocols/ABCs

2. **Specific Checks:**
   - Check all files for `ChromaDB()` direct calls vs. using abstraction
   - Look for `ChatOpenAI()`, `ChatAnthropic()` etc. direct usage vs. `get_model()`
   - Check if tools instantiate MCP clients directly vs. using factory/injection

3. **Inversion Failures**
   - High-level policy modules importing low-level implementation details
   - Business logic importing database/HTTP specifics

4. **Good Patterns to Verify:**
   - `MCPClient` ABC usage throughout
   - `BaseAgent` abstraction usage
   - `MarketGatherer` base class usage

**Questions to Ask:**
- "Does this module import concrete implementations?"
- "Could this function work with a protocol instead of a concrete class?"
- "Are dependencies passed in vs. created internally?"

---

### Phase 3: KISS (Keep It Simple, Stupid)

**Search for:**

1. **Over-Engineering**
   - Design patterns used where a function would suffice
   - Multiple layers of abstraction for simple operations
   - Metaclasses, descriptors, or decorators for simple needs

2. **Unnecessary Complexity**
   - Nested conditionals 4+ levels deep
   - Complex type gymnastics for simple data structures
   - Overuse of async/await for I/O-bound but simple operations

3. **Specific Checks:**
   - `agents/blackboard/` — is the blackboard pattern necessary complexity?
   - `agents/middleware/` — is two-pass synthesis over-engineering?
   - `llm/model_selection.py` — is the provider/model selection logic appropriately simple?
   - `utils/security.py` — are TOCTOU protections necessary or overkill?

4. **Clever Code**
   - List comprehensions with 3+ nested conditions
   - Lambda chains or functional programming for simple loops
   - Metaprogramming that could be explicit code

5. **Configuration Complexity**
   - Too many configuration options that are rarely used
   - Complex environment variable parsing for simple defaults

**Questions to Ask:**
- "Could this be written in half the lines?"
- "Is this abstraction used in 3+ places or just one?"
- "Would a junior developer understand this in 30 seconds?"
- "Am I solving a problem we might have vs. one we do have?"

---

### Phase 4: YAGNI (You Aren't Gonna Need It)

**Search for:**

1. **Unused Code**
   - Functions/classes with no callers in the codebase
   - Parameters that are always `None` or have the same value
   - Features behind flags that are never enabled

2. **Premature Generalization**
   - Abstract base classes with only one subclass
   - Generic implementations when one concrete case exists
   - Configuration options for hypothetical deployments

3. **Specific Checks:**
   - Scan for `# TODO:` or `# FIXME:` comments for features not implemented
   - Look for `if FEATURE_X:` blocks where FEATURE_X is never true
   - Check for unused imports (dead code)
   - Look for commented-out code blocks

4. **Over-Configurability**
   - Constants in `constants.py` that are used once
   - Settings in `config.py` that are never referenced
   - Prompt templates with variables that are always the same value

5. **Defensive Programming Excess**
   - Validation for impossible states
   - Error handling for exceptions that can't occur
   - Null checks for non-nullable values

**Questions to Ask:**
- "Has this code been executed in the last 6 months?"
- "Is this abstraction preparing for a future that may not come?"
- "Could this be added when actually needed vs. now?"
- "Is this test covering a scenario that can't happen?"

---

## Execution Instructions

### Step 1: File-by-File Analysis

For each Python file in `src/fu7ur3pr00f/`:

1. Read the entire file
2. Identify its primary responsibility
3. List all imports (check for unused)
4. Map all public functions/methods
5. Check for code smells per principle above
6. Note line numbers for every violation

### Step 2: Cross-File Pattern Analysis

After individual file review:

1. Compare similar files (specialists, MCP clients, gatherers, tools)
2. Look for copy-paste patterns across files
3. Check if abstractions are consistently used
4. Identify modules that should share more code

### Step 3: Test Coverage Check

For each violation found:

1. Check if tests exist in `tests/` mirror directory
2. Note if refactoring would break tests
3. Identify tests that may be testing implementation vs. behavior

### Step 4: Prioritized Findings Report

Format each finding as:

```markdown
## [SEVERITY: High/Medium/Low] Principle Violation

**Location**: `src/fu7ur3pr00f/path/to/file.py:line_number`

**Issue**: Clear description of the violation

**Code**:
```python
# Show the problematic code (3-10 lines)
```

**Why It Violates [PRINCIPLE]**: Explanation

**Impact**: What problems this causes (maintenance, testing, extensibility)

**Recommendation**: Specific refactoring suggestion

**Related Files**: Other files affected or similar violations
```

---

## Severity Classification

**High**:
- Violations that cause tight coupling
- DRY violations with 3+ duplicates
- SOLID violations that prevent testing
- Dead code with security implications

**Medium**:
- DRY violations with 2 duplicates
- Minor SOLID violations (ISP mostly)
- Over-engineering that adds cognitive load
- Unused parameters or configuration

**Low**:
- Style inconsistencies
- Minor KISS violations (slightly clever code)
- Comments that could be clearer
- Premature optimization with no cost

---

## Deliverables

1. **Executive Summary**: Top 10 most critical violations
2. **Detailed Findings**: All violations organized by principle
3. **Quick Wins**: Violations fixable in <30 minutes each
4. **Refactoring Plan**: Phased approach for larger changes
5. **Test Impact**: Which tests need updates for each fix

---

## Special Focus Areas

Based on the architecture, pay extra attention to:

1. **Specialist Consistency**: All 5 specialists should follow identical patterns
2. **MCP Client Uniformity**: 12 clients should have minimal duplication
3. **Tool Registration**: 41 tools should use consistent patterns
4. **Memory Abstraction**: Knowledge vs. episodic stores should share appropriately
5. **Middleware Composition**: Check if middleware chain is composable or coupled
6. **Prompt Consistency**: 31 prompt files should follow templates
7. **Error Handling**: Should be centralized, not duplicated

---

## Anti-Patterns to Flag Immediately

🚩 **Red Flags** (report these first):

- Circular imports between modules
- Direct ChromaDB instantiation outside `memory/`
- Hardcoded API keys or secrets
- Synchronous HTTP calls in async contexts
- Tools that modify global state
- Missing error handling for external service calls
- Prompts with hardcoded model-specific instructions
- Tests that make real API calls

---

## Final Check

Before concluding, verify:

- [ ] Every Python file in `src/fu7ur3pr00f/` has been analyzed
- [ ] All 41 tools have been reviewed for consistency
- [ ] All 12 MCP clients have been compared
- [ ] All 5 specialists have been cross-checked
- [ ] All 31 prompts have been scanned for duplication
- [ ] Test files mirror source structure appropriately
- [ ] No violation appears in the report twice (consolidate duplicates)

---

**Begin the audit now. Be thorough, be specific, and cite exact line numbers.**
