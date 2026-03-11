#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/fresh_install_check.sh [--source local|pypi] [--config-from PATH] [--keep]

Runs an isolated pipx install and executes fu7ur3pr00f diagnostics.

Options:
  --source       Install source: "local" (default) or "pypi"
  --config-from  Path to an .env file to copy into the isolated HOME
  --keep         Keep temp directory for inspection
USAGE
}

source_mode="local"
config_from=""
keep="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      source_mode="${2:-}"
      shift 2
      ;;
    --config-from)
      config_from="${2:-}"
      shift 2
      ;;
    --keep)
      keep="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "$source_mode" != "local" && "$source_mode" != "pypi" ]]; then
  echo "Invalid --source: $source_mode"
  usage
  exit 1
fi

if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx is required. Install it first: python -m pip install --user pipx"
  exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
real_home="${HOME}"
temp_root="$(mktemp -d)"
temp_home="${temp_root}/home"
pipx_home="${temp_root}/pipx"
pipx_bin="${temp_root}/bin"

mkdir -p "${temp_home}" "${pipx_home}" "${pipx_bin}"
export HOME="${temp_home}"
export PIPX_HOME="${pipx_home}"
export PIPX_BIN_DIR="${pipx_bin}"

cleanup() {
  if [[ "$keep" != "true" ]]; then
    rm -rf "${temp_root}"
  else
    echo "Kept temp directory: ${temp_root}"
  fi
}
trap cleanup EXIT

if [[ -n "$config_from" ]]; then
  if [[ ! -f "$config_from" ]]; then
    echo "Config file not found: $config_from"
    exit 1
  fi
  mkdir -p "${HOME}/.fu7ur3pr00f"
  cp "${config_from}" "${HOME}/.fu7ur3pr00f/.env"
fi

if [[ -d "${real_home}/.config/glab-cli" ]]; then
  mkdir -p "${HOME}/.config"
  cp -R "${real_home}/.config/glab-cli" "${HOME}/.config/"
fi

if [[ "$source_mode" == "local" ]]; then
  pipx install "${repo_root}"
else
  pipx install fu7ur3pr00f
fi

venv_python="${PIPX_HOME}/venvs/fu7ur3pr00f/bin/python"
if [[ ! -x "$venv_python" ]]; then
  echo "Could not find pipx venv python at: $venv_python"
  exit 1
fi

echo "Running diagnostics in isolated environment..."
if ! "$venv_python" - <<'PY' >/dev/null 2>&1
import importlib.util
spec = importlib.util.find_spec("fu7ur3pr00f.diagnostics")
raise SystemExit(0 if spec else 1)
PY
then
  echo "Diagnostics module not found in installed package."
  echo "If using --source pypi, publish a release that includes fu7ur3pr00f.diagnostics."
  exit 2
fi

"$venv_python" -m fu7ur3pr00f.diagnostics
