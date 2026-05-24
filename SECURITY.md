# Security

## Trust Model

fu7ur3pr00f assumes a **trusted local environment**. All services bind to `127.0.0.1` only.

## Rules

See `AGENTS.md` for security-related coding standards:
- Never hardcode secrets or credentials
- Never commit `.env` files
- Use environment variables for sensitive configuration

## Reporting

Report security issues directly to the project maintainers. Do not open public issues for vulnerabilities.