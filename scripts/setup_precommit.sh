#!/bin/bash

# Setup script for pre-commit hooks
set -e  # Exit on any error

echo "Setting up pre-commit hooks..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install the git hooks
pre-commit install

# Run on all files to make sure everything is clean
echo "Running pre-commit on all files..."
pre-commit run --all-files

echo "Pre-commit hooks installed successfully!"
echo "Hooks will now run automatically on 'git commit'"