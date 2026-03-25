#!/usr/bin/env python3
"""
Test runner script for validating code before commit.
Used by pre-commit hook to run tests and report status.
"""

import subprocess
import sys


def run_tests():
    """Run tests and return success status."""
    try:
        # Run pytest with minimal output for faster feedback
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-x",  # Stop on first failure
                "--tb=short",
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print("Tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False

        print("All tests passed!")
        return True

    except subprocess.TimeoutExpired:
        print("Tests timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_lint():
    """Run linting and return success status."""
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "flake8",
                ".",
                "--exclude=node_modules,.git,__pycache__,.tox",
                "--max-line-length=88",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("Linting found issues:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False

        print("Linting passed!")
        return True

    except Exception as e:
        print(f"Error running linter: {e}")
        return False


def run_type_check():
    """Run type checking and return success status."""
    try:
        # Try pyright first
        result = subprocess.run(["npx", "pyright"], capture_output=True, text=True)

        if result.returncode != 0:
            print("Type checking (pyright) found issues:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False

        print("Type checking (pyright) passed!")

        # Also run mypy
        result = subprocess.run(["mypy"], capture_output=True, text=True)

        if result.returncode != 0:
            print("Type checking (mypy) found issues:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False

        print("Type checking (mypy) passed!")
        return True

    except Exception as e:
        print(f"Error running type checker: {e}")
        return False


def main():
    """Main function to run all validations."""
    print("Running pre-commit validations...")

    all_passed = True

    # Run type checking
    if not run_type_check():
        all_passed = False

    # Run linting
    if not run_lint():
        all_passed = False

    # Run tests
    if not run_tests():
        all_passed = False

    if not all_passed:
        print("\n❌ Pre-commit validation failed!")
        sys.exit(1)
    else:
        print("\n✅ All pre-commit validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
