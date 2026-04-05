#!/usr/bin/env bash
set -euo pipefail

# Remove build artifacts so the tree reflects only tracked source files.
rm -rf dist build

# Remove Python cache directories and bytecode files that accumulate during development.
# Security: Log errors instead of silently suppressing them
find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>&1 | while read -r line; do
  echo "[WARN] clean_dev: ${line}" >&2
done || true

find . -name "*.pyc" -delete 2>&1 | while read -r line; do
  echo "[WARN] clean_dev: ${line}" >&2
done || true

# Optionally purge transient market cache to force fresh data.
if [[ -d "data/cache" ]]; then
  rm -rf data/cache 2>&1 | while read -r line; do
    echo "[WARN] clean_dev: ${line}" >&2
  done || true
  echo "[INFO] Market cache cleared"
fi
