#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/run_vagrant_apt_smoke.sh [ubuntu2404|debian12|all] [--destroy]

Boots one or more Vagrant VMs from vagrant/Vagrantfile and runs the public apt
install/reinstall/remove/purge smoke test inside each VM.

Examples:
  scripts/run_vagrant_apt_smoke.sh ubuntu2404
  scripts/run_vagrant_apt_smoke.sh all --destroy

Notes:
  - Requires Vagrant and a provider such as VirtualBox.
  - To use another provider, set VAGRANT_DEFAULT_PROVIDER before running.
USAGE
}

target="${1:-all}"
destroy_after="false"

for arg in "$@"; do
  case "${arg}" in
    ubuntu2404|debian12|all)
      target="${arg}"
      ;;
    --destroy)
      destroy_after="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: ${arg}" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v vagrant >/dev/null 2>&1; then
  echo "vagrant is required." >&2
  exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vagrant_dir="${repo_root}/vagrant"

if [[ ! -f "${vagrant_dir}/Vagrantfile" ]]; then
  echo "Missing Vagrantfile at ${vagrant_dir}/Vagrantfile" >&2
  exit 1
fi

machines=()
case "${target}" in
  ubuntu2404|debian12)
    machines=("${target}")
    ;;
  all)
    machines=(ubuntu2404 debian12)
    ;;
  *)
    echo "Invalid target: ${target}" >&2
    usage
    exit 1
    ;;
esac

pushd "${vagrant_dir}" >/dev/null
for machine in "${machines[@]}"; do
  echo "Running Vagrant apt smoke test in ${machine}"
  vagrant up "${machine}" --provision
  if [[ "${destroy_after}" == "true" ]]; then
    vagrant destroy -f "${machine}"
  fi
done
popd >/dev/null
