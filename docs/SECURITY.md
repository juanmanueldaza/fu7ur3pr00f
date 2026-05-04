# Security

fu7ur3pr00f operates in a **trusted local environment** — single user, local filesystem, no network listeners. Security boundaries protect against accidental misuse and malicious input files.

## Trust Model

- **Assumption**: The user is trusted. The machine is trusted. The opencode process is trusted.
- **Threat model**: Malicious or malformed input files (ZIP archives, PDFs, HTML, JSON). Accidental PII leakage through prompts or logs. SSRF through portfolio scraping. Path traversal through archive extraction.
- **Not in scope**: Multi-user access control, network authentication, encrypted storage, sandboxing.

## File I/O Security

All file operations use safe patterns from `src/fu7ur3pr00f/utils/security.py`:

| Function | Protection |
|----------|-----------|
| `secure_open(path, mode, file_mode=0o600)` | `os.open()` + `os.fchmod()` before first write. No TOCTOU window between creation and permission set. |
| `secure_mkdir(path, mode=0o700)` | Directory creates with restrictive permissions. |
| `validate_file_size(path, max_size, label)` | Reject files exceeding size limits before reading. |

Profile YAML (`~/.fu7ur3pr00f/profile.yaml`) is read and written atomically through `edit_profile()` with a `threading.Lock()` — no read-modify-write races.

## PII Handling

`anonymize_career_data()` applies 12 regex patterns in order-dependent processing (specific before general) to scrub:

- Email addresses (with optional preservation of professional emails)
- Phone numbers (4 international formats)
- Physical addresses
- Social media profile URLs
- SSN, DOB (labeled only), IBAN, bank accounts
- Passport numbers, driver's license numbers

Email anonymization is applied to LinkedIn Connections CSV during import. PII detection is a **best-effort regex scan** — not a substitute for manual review before sharing analysis output.

## Prompt Injection Protection

| Protection | Implementation |
|-----------|---------------|
| XML boundary escape | `sanitize_for_prompt()` escapes `</tag>` → `<\/tag>` preventing XML injection into LLM prompt boundaries |
| API key redaction | `sanitize_error()` strips OpenAI, Anthropic, Google, and Bearer token patterns from error messages before display |
| Secret masking | `mask_secret(value, visible_chars=4)` shows only first 4 characters: `sk-a...5678` |

## SSRF Protection (Portfolio Gatherer)

The portfolio fetcher (`gatherers/portfolio/fetcher.py`) implements a comprehensive SSRF defense:

| Protection | Implementation |
|-----------|---------------|
| DNS pinning | Hostname resolved once, all subsequent connection attempts use the resolved IP |
| Private/CGNAT blocking | RFC 6598 addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10, 127.0.0.0/8, ::1, fc00::/7) are rejected |
| Redirect validation | Each hop re-validated for SSRF before following |
| Redirect limit | Maximum 5 redirects |
| URL length limit | Maximum 2048 characters |
| Response size limit | Maximum 10MB |
| Content-type validation | JSON content verified before parsing |

## Archive Security

| Input Type | Protection |
|-----------|-----------|
| ZIP archives | Size bomb detection (500MB uncompressed limit). Path traversal check on every entry name. |
| PDF files | Magic byte validation (`%PDF`). Size limit (10MB for CV, 50MB for CliftonStrengths). |
| JSON data | 1MB size limit, `json.loads()` only (no eval). |

## Error Safety

- `NoDataError` — raised when input is empty or unparseable, caught by gather scripts with user-friendly messages.
- `ServiceError` — raised when system dependencies are missing (e.g., `pdftotext` for PDF parsing).
- Structured error messages include the component that failed and actionable next steps.
- No stack traces leak to end users — errors are logged at DEBUG level to file, WARNING+ to console.

## Attack Surface Summary

| Vector | Exposure | Mitigation | Status |
|--------|---------|-----------|--------|
| Malicious ZIP | LinkedIn gatherer input | 500MB limit, path traversal check | ✓ |
| Malicious PDF | CliftonStrengths, CV input | Magic byte check, size limit | ✓ |
| Malicious HTML | Portfolio scraper input | BeautifulSoup parse, no eval | ✓ |
| SSRF via portfolio URL | Portfolio fetcher | DNS pinning, private IP block, redirect validation | ✓ |
| PII in LLM prompts | Generated prompts | Regex scrubbing, optional email preservation | ✓ |
| Prompt injection via career data | Prompt templates | XML boundary escaping | ✓ |
| API key leakage | Error messages | Pattern-based redaction | ✓ |
| TOCTOU file writes | All file output | `os.open()` + `os.fchmod()` | ✓ |
| Thread race on profile | Profile editing | `threading.Lock()` read-modify-write | ✓ |
