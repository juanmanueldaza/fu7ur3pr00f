# Development Workflow

This document outlines the development workflow and validation processes for maintaining code quality.

## Pre-commit Hooks Setup

We use pre-commit hooks to enforce code quality standards before each commit. To set up:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
./scripts/setup_precommit.sh
```

After installation, these hooks will automatically run on every `git commit` and prevent commits that don't meet our quality standards.

## Validation Checks Performed

### 1. Code Formatting (Black)
- Ensures consistent code style
- Enforces 88-character line length
- Standardizes formatting across the codebase

### 2. Import Sorting (isort)
- Organizes imports consistently
- Groups standard library, third-party, and local imports
- Compatible with Black formatting

### 3. Linting (Flake8)
- Checks for common Python errors and style issues
- Enforces PEP 8 compliance
- Includes security checks via flake8-bugbear

### 4. Type Checking
- **Pyright**: Microsoft's static type checker for Python
- **MyPy**: Gradual type checker for Python
- Both ensure type safety and catch potential runtime errors

### 5. Security Scanning (Bandit)
- Identifies common security issues in Python code
- Focuses on high and medium severity findings

### 6. Tests (Pytest)
- Runs all project tests
- Ensures new changes don't break existing functionality
- Stops on first failure for faster feedback

## Manual Validation

To run all validation checks manually:

```bash
# Run all pre-commit checks on all files
pre-commit run --all-files

# Or run the test script directly
python scripts/run_tests.py
```

## Configuration Files

- `pyrightconfig.json`: Pyright type checker configuration
- `mypy.ini`: MyPy type checker configuration  
- `.pre-commit-config.yaml`: Pre-commit hook definitions
- `setup.cfg`: Flake8, pytest, and isort configurations

## Bypassing Pre-commit (Use Sparingly)

In emergency situations, you can bypass pre-commit checks:

```bash
git commit --no-verify
```

However, this should only be done when absolutely necessary and followed by immediate correction of any violations.

## Troubleshooting

If you encounter issues with pre-commit hooks:

1. Ensure all development dependencies are installed:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Check Node.js is installed (required for Pyright):
   ```bash
   node --version
   npm install -g pyright
   ```

3. Update pre-commit hooks:
   ```bash
   pre-commit autoupdate
   ```