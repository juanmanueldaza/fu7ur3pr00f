# Security Quick Reference Card

**Print this. Bookmark it. Share it.** 🔐

---

## 🔴 CRITICAL FIXES (DO FIRST — Week 1)

### H1: Specialist Data Sanitization
```python
# File: agents/specialists/base.py:248
# Fix: Wrap values with sanitize_for_prompt()

from ..utils.security import sanitize_for_prompt
safe_value = sanitize_for_prompt(str(value))
```

### H2: Synthesis Node Sanitization  
```python
# File: agents/blackboard/graph.py:173
# Fix: Sanitize all findings before synthesis prompt

safe_reasoning = sanitize_for_prompt(str(finding['reasoning']))
```

### H3: ZIP Bomb Protection
```python
# File: gatherers/linkedin.py
# Fix: Validate ZIP before extraction

MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB
# Check ZipInfo.file_size before extraction
```

### M1: Iteration Hard-Cap
```python
# File: agents/blackboard/scheduler.py:43
# Fix: Clamp max_iterations to 3

if max_iterations > MAX_ITERATIONS_HARD_CAP:
    max_iterations = MAX_ITERATIONS_HARD_CAP
```

### M5: HTML Sanitization
```python
# File: generators/cv_generator.py:62
# Fix: Sanitize HTML before rendering

import bleach
sanitized_html = bleach.clean(html_content, tags=ALLOWED_TAGS, strip=True)
```

---

## 🟡 HIGH PRIORITY FIXES (Week 2)

| Issue | File | Fix |
|-------|------|-----|
| **M7** Thread IDs | `executor.py:94` | Use `uuid.uuid4().hex` instead of `time.time()` |
| **M4** Error Messages | `graph.py:96` | Use `_sanitize_error(e)` before streaming |
| **M2** Truncation Logging | `base.py:187` | Add `logger.warning()` when truncating |

---

## 🟢 MEDIUM PRIORITY (Week 3)

| Issue | File | Fix |
|-------|------|-----|
| **M3** Metadata Keys | `episodic.py:44` | Validate keys against `ALLOWED_METADATA_KEYS` |
| **L1-L5** Documentation | Various | Add docstrings, bounds checks, documentation |

---

## 📋 Quick Checklist

### Before You Code
- [ ] Read `OWASP_SECURITY_AUDIT.md` (full details)
- [ ] Read `SECURITY_IMPLEMENTATION_GUIDE.md` (step-by-step)
- [ ] Check this card (quick overview)

### While Coding
- [ ] Apply fix from implementation guide
- [ ] Write test for the fix
- [ ] Run: `pytest tests/ -q`
- [ ] Run: `ruff check src/`
- [ ] Run: `pyright src/fu7ur3pr00f`

### Before Committing
- [ ] Tests pass locally
- [ ] No regressions: `pytest tests/ -q`
- [ ] Security tests pass: `pytest tests/test_*security*.py -v`
- [ ] Docstring updated
- [ ] No hardcoded secrets/paths in code

### After Merge
- [ ] Update status tracker in `SECURITY_REMEDIATION_CHECKLIST.md`
- [ ] Run full suite: `pytest tests/ --cov=src/fu7ur3pr00f`

---

## 🧪 Testing Commands

```bash
# Single fix verification
pytest tests/test_prompt_injection.py -v

# All security tests
pytest tests/ -k "security" -v

# Coverage
pytest tests/ --cov=src/fu7ur3pr00f --cov-report=term-missing

# Linting
ruff check src/ --fix

# Type checking
pyright src/fu7ur3pr00f

# Everything
pytest tests/ -q && ruff check src/ && pyright src/fu7ur3pr00f
```

---

## 🚨 Common Pitfalls to Avoid

❌ **DON'T:** Forget to sanitize specialist findings  
✅ **DO:** Use `sanitize_for_prompt()` on all cross-specialist data

❌ **DON'T:** Allow unbounded iterations  
✅ **DO:** Hard-cap `max_iterations` to 3

❌ **DON'T:** Extract ZIPs without validation  
✅ **DO:** Check sizes first, reject if >500MB total

❌ **DON'T:** Render raw HTML from LLM  
✅ **DO:** Sanitize with `bleach` before weasyprint

❌ **DON'T:** Use timestamp-based IDs  
✅ **DO:** Use `uuid.uuid4().hex`

❌ **DON'T:** Stream raw exception messages  
✅ **DO:** Use `_sanitize_error()` before streaming

---

## 📞 Quick Questions?

| Q | A |
|---|---|
| **Where's the full audit?** | `OWASP_SECURITY_AUDIT.md` |
| **How do I implement fix X?** | `SECURITY_IMPLEMENTATION_GUIDE.md` |
| **What's the priority order?** | `SECURITY_REMEDIATION_CHECKLIST.md` |
| **What's the overall status?** | `SECURITY_SUMMARY.md` |
| **Is this urgent?** | Yes, 3 HIGH findings (H1, H2, H3) |

---

## 🎯 Success Criteria

✅ **Done When:**
- All tests pass: `pytest tests/ -q`
- No linting errors: `ruff check src/` 
- No type errors: `pyright src/fu7ur3pr00f`
- All security tests pass: `pytest tests/ -k "security" -v`
- Risk rating improves from 🟡 MEDIUM → 🟢 LOW

---

## 📊 Risk Summary

```
BEFORE:
🔴 3 HIGH   (H1, H2, H3)
🟡 7 MEDIUM (M1-M7)
🟢 5 LOW    (L1-L5)
RISK: MEDIUM

AFTER:
🟢 0 HIGH
🟢 0 MEDIUM
🟢 0 LOW (all improved)
RISK: LOW
```

---

## 🔑 Key Utilities

Already implemented in `utils/security.py`:

```python
from fu7ur3pr00f.utils.security import:
  - sanitize_for_prompt()        # Escape XML closing tags
  - anonymize_career_data()      # PII removal
  - secure_open()                # Atomic file permissions
  - secure_mkdir()               # Restrictive directory permissions
```

**Use them!** They're already tested and secure.

---

**Last Updated:** March 26, 2026  
**Print Date:** ___________  
**Reviewer:** ___________
