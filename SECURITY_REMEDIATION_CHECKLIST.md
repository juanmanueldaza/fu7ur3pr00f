# Security Remediation Checklist

**Status:** 🔴 0/10 Completed  
**Priority:** Critical + High findings must be fixed before production  
**Timeline:** 3 weeks (Week 1: critical, Week 2-3: medium/low)

---

## CRITICAL PATH (Week 1)

### [ ] H1. Blackboard Cross-Specialist Data Poisoning

**File:** `agents/specialists/base.py:240-253`

**Action:**
1. Import `sanitize_for_prompt` from `utils.security`
2. Wrap all specialist finding values with `sanitize_for_prompt()` in `_format_previous_findings()`
3. Add `max_length` constraints to `SpecialistFindingsModel` fields
4. Write test: `tests/test_prompt_injection.py::test_specialist_findings_sanitized`

**Code Change:**
```python
# Before
context_parts.append(f"  - {key}: {value}")

# After
from ..utils.security import sanitize_for_prompt
safe_value = sanitize_for_prompt(str(value))
context_parts.append(f"  - {key}: {safe_value}")
```

**Verification:**
```bash
pytest tests/test_prompt_injection.py -v
```

---

### [ ] H2. Synthesis Node Prompt Injection

**File:** `agents/blackboard/graph.py:173-200`

**Action:**
1. Apply `sanitize_for_prompt()` to all finding values in synthesis node
2. Consider JSON structure instead of markdown for findings
3. Add [NOTE] prefix to mark findings as untrusted
4. Write test: `tests/test_blackboard_security.py::test_synthesis_sanitization`

**Code Change:**
```python
# Before
parts.append(f"**Summary:** {finding['reasoning']}")

# After
from ..utils.security import sanitize_for_prompt
safe_reasoning = sanitize_for_prompt(str(finding['reasoning']))
parts.append(f"**Summary:** {safe_reasoning}")
```

**Verification:**
```bash
pytest tests/test_blackboard_security.py::test_synthesis_sanitization -v
```

---

### [ ] H3. ZIP Bomb / Decompression Bomb

**File:** `gatherers/linkedin.py:580-600`

**Action:**
1. Add `_validate_zip_archive()` function to check sizes before extraction
2. Set thresholds: 500MB total, 100MB per file, 100 entries max
3. Call validation before `zipfile.ZipFile()` extraction
4. Write test: `tests/test_linkedin_zip_validation.py::test_zip_bomb_detection`

**Code Change:**
```python
# Before
with zipfile.ZipFile(zip_path, "r") as zf:
    for tier, csv_name, parser, use_variants in _CSV_PARSERS:
        rows = _read_csv(zf, csv_name)

# After
_validate_zip_archive(zip_path)  # NEW
with zipfile.ZipFile(zip_path, "r") as zf:
    # ... same as before ...
```

**Verification:**
```bash
pytest tests/test_linkedin_zip_validation.py -v
```

---

### [ ] M5. HTML/CSS Injection in CV PDF

**File:** `generators/cv_generator.py:60-100`

**Action:**
1. Add `bleach==6.0.0` to `requirements.txt`
2. Import bleach in `_render_pdf()`
3. Sanitize HTML output after markdown conversion
4. Define ALLOWED_TAGS and ALLOWED_ATTRS
5. Write test: `tests/test_cv_generator_sanitization.py::test_html_injection_prevention`

**Code Change:**
```python
# Before
html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
styled_html = f"...{html_content}..."

# After
import bleach
html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
sanitized_html = bleach.clean(
    html_content,
    tags={"h1", "h2", "h3", "p", "strong", "em", "ul", "ol", "li", "table", "td", "th", "tr", "code", "pre"},
    attributes={"a": ["href", "title"]},
    strip=True,
)
styled_html = f"...{sanitized_html}..."
```

**Verification:**
```bash
pip install bleach==6.0.0
pytest tests/test_cv_generator_sanitization.py -v
```

---

### [ ] M1. Hard-Cap Blackboard Iterations

**File:** `agents/blackboard/scheduler.py:43-55`

**Action:**
1. Define `MAX_ITERATIONS_HARD_CAP = 3` constant
2. Clamp `max_iterations` in `__init__` with warning log
3. Write test: `tests/test_blackboard_security.py::test_iterations_hard_capped`

**Code Change:**
```python
# Before
def __init__(self, strategy: str = "linear", max_iterations: int = 1, execution_order: list[str] | None = None):
    self.strategy = strategy
    self.max_iterations = max_iterations

# After
MAX_ITERATIONS_HARD_CAP = 3

def __init__(self, strategy: str = "linear", max_iterations: int = 1, execution_order: list[str] | None = None):
    self.strategy = strategy
    if max_iterations > MAX_ITERATIONS_HARD_CAP:
        logger.warning("max_iterations clamped to %d", MAX_ITERATIONS_HARD_CAP)
        self.max_iterations = MAX_ITERATIONS_HARD_CAP
    else:
        self.max_iterations = max_iterations
```

**Verification:**
```bash
pytest tests/test_blackboard_security.py::test_iterations_hard_capped -v
```

---

## HIGH PRIORITY (Week 2)

### [ ] M7. Replace Timestamp-Based Thread IDs with UUID

**File:** `agents/blackboard/executor.py:94`

**Action:**
1. Import `uuid`
2. Replace `f"bb_{int(time.time() * 1000)}"` with `f"bb_{uuid.uuid4().hex}"`
3. Write test: `tests/test_blackboard_security.py::test_thread_id_is_random`

**Code Change:**
```python
# Before
config = {"configurable": {"thread_id": f"bb_{int(time.time() * 1000)}"}}

# After
import uuid
config = {"configurable": {"thread_id": f"bb_{uuid.uuid4().hex}"}}
```

**Verification:**
```bash
pytest tests/test_blackboard_security.py::test_thread_id_is_random -v
```

---

### [ ] M4. Sanitize Error Messages in Stream Events

**File:** `agents/blackboard/graph.py:96-97`

**Action:**
1. Import `_sanitize_error()` from chat client (or create if missing)
2. Wrap `str(e)` with `_sanitize_error(e)` before streaming
3. Add logging of raw error for internal debugging
4. Write test: `tests/test_blackboard_security.py::test_error_messages_sanitized`

**Code Change:**
```python
# Before
stream_writer({
    "type": "specialist_error",
    "specialist": specialist_name,
    "error": str(e),
})

# After
from ..chat.client import _sanitize_error
logger.exception("Specialist %s failed", specialist_name)  # Log raw error
stream_writer({
    "type": "specialist_error",
    "specialist": specialist_name,
    "error": _sanitize_error(e),  # Sanitize for UI
})
```

**Verification:**
```bash
pytest tests/test_blackboard_security.py::test_error_messages_sanitized -v
```

---

## MEDIUM PRIORITY (Week 3)

### [ ] M2. Log Tool Result Truncations

**File:** `agents/specialists/base.py:187`

**Action:**
1. Add `logger.warning()` when result is truncated
2. Consider preserving end-of-result by middle-truncation
3. Write test: `tests/test_specialists.py::test_tool_result_truncation_logged`

**Code Change:**
```python
# Before
result_str = str(result)[:3000]

# After
TOOL_RESULT_MAX_CHARS = 3000
if len(result_str) > TOOL_RESULT_MAX_CHARS:
    logger.warning("Tool result truncated: %s returned %d chars", tool_name, len(result_str))
    result_str = result_str[:TOOL_RESULT_MAX_CHARS]
```

---

### [ ] M3. Validate ChromaDB Metadata Keys

**File:** `memory/episodic.py:44-52`

**Action:**
1. Define `ALLOWED_METADATA_KEYS` set
2. Validate user-supplied metadata keys against allowlist
3. Type-check metadata values
4. Write test: `tests/test_memory.py::test_metadata_key_validation`

**Code Change:**
```python
# Before
metadatas=[{
    "decision_type": "career_pivot",
    "timestamp": datetime.now().isoformat(),
    **(metadata or {}),
}],

# After
ALLOWED_METADATA_KEYS = {"specialist", "iteration", "confidence", "source", "tags"}

def store_decision(self, context: str, decision: str, metadata: dict[str, Any] | None = None):
    if metadata:
        invalid_keys = set(metadata.keys()) - ALLOWED_METADATA_KEYS
        if invalid_keys:
            raise ValueError(f"Invalid metadata keys: {invalid_keys}")
    
    validated = {
        "decision_type": "career_pivot",
        "timestamp": datetime.now().isoformat(),
        **(metadata or {}),
    }
```

---

## LOW PRIORITY

### [ ] L1. Confidence Score Bounds Enforcement

**File:** `agents/blackboard/blackboard.py:155`

**Action:** Add explicit bounds check in `record_specialist_contribution()`:
```python
if not 0.0 <= confidence <= 1.0:
    raise ValueError(f"Confidence must be in [0.0, 1.0], got {confidence}")
```

---

### [ ] L2-L5. Documentation Improvements

**Actions:**
- L2: Document truncation behavior in `_format_previous_findings()` docstring
- L3: Document async assumptions in `DynamicPromptMiddleware`
- L4: Optimize regex in `_clean_llm_output()`
- L5: No action needed (bounded by M1 mitigation)

---

## Testing Checklist

### Create New Test Files

- [ ] `tests/test_prompt_injection.py` — H1, H2
- [ ] `tests/test_linkedin_zip_validation.py` — H3
- [ ] `tests/test_cv_generator_sanitization.py` — M5
- [ ] `tests/test_blackboard_security.py` — M1, M4, M7

### Add Tests to Existing Files

- [ ] `tests/test_specialists.py` — M2
- [ ] `tests/test_memory.py` — M3

### Run Full Test Suite

```bash
# Install security test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v --cov=src/fu7ur3pr00f --cov-report=term-missing

# Run security-specific tests
pytest tests/test_prompt_injection.py tests/test_blackboard_security.py tests/test_linkedin_zip_validation.py tests/test_cv_generator_sanitization.py -v
```

---

## CI/CD Integration

### Add Security Scanning

Create `.github/workflows/security.yml`:

```yaml
name: Security Checks
on: [push, pull_request]

jobs:
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit
        run: pip install bandit && bandit -r src/ -ll

  safety:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check Dependencies
        run: pip install safety && safety check

  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.13"
      - run: pip install -e . && pytest tests/test_*security*.py -v
```

---

## Verification Steps

### Before Marking as Complete

1. **Code Review:** Security-focused code review for each PR
2. **Testing:** All new security tests pass (`pytest -v`)
3. **Linting:** `ruff check .` and `pyright` pass
4. **Manual Testing:** Test remediations in development environment
5. **Documentation:** Update CHANGELOG.md with security fixes

### Example Verification Command

```bash
# After implementing all fixes
pytest tests/ -v --cov=src/fu7ur3pr00f
ruff check src/
pyright src/fu7ur3pr00f
```

---

## Sign-Off

| Milestone | Target | Status | Notes |
|-----------|--------|--------|-------|
| Week 1: H1, H2, H3, M1, M5 | 2026-04-02 | 🔴 TO DO | Critical path |
| Week 2: M4, M7, M2 | 2026-04-09 | 🔴 TO DO | High priority |
| Week 3: M3, L1-L5 | 2026-04-16 | 🔴 TO DO | Low priority |
| **Final Audit** | 2026-04-16 | 🔴 TO DO | Re-audit after fixes |

---

**Document Generated:** March 26, 2026  
**Next Review:** After all remediations complete
