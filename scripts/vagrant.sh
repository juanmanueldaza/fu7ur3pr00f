#!/usr/bin/env bash
set -euo pipefail

# Unified Vagrant management script
# Security: All variables quoted, VM names validated against allowlist

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
vagrant_dir="${repo_root}/vagrant"

# Security: Allowlist of valid VM names
VALID_VMS=("dev" "ubuntu2404" "debian12")

is_valid_vm() {
  local vm="$1"
  for valid in "${VALID_VMS[@]}"; do
    if [[ "${vm}" == "${valid}" ]]; then
      return 0
    fi
  done
  return 1
}

usage() {
  cat <<'EOF'
Vagrant management for FutureProof

Usage: scripts/vagrant.sh COMMAND [OPTIONS]

Commands:
  dev          Start development VM (default)
  test-apt     Test apt repo from GitHub Pages on Ubuntu + Debian
  multi        Test multi-agent system in dev VM
  ssh [VM]     SSH into VM (default: dev)
  status       Show all VMs and resource usage
  halt [VM]    Stop VM(s) to save resources
  clean        Destroy test VMs (keeps dev)
  destroy      Destroy ALL VMs
  logs         Show dev VM provision logs

Examples:
  scripts/vagrant.sh              # Start dev VM
  scripts/vagrant.sh test-apt     # Test published apt repo
  scripts/vagrant.sh multi        # Test multi-agent chat
  scripts/vagrant.sh halt         # Stop all VMs
  scripts/vagrant.sh clean        # Remove test VMs only

VMs:
  dev         Development environment (4GB RAM, synced folders)
  ubuntu2404  Apt testing on Ubuntu 24.04 (2GB RAM)  
  debian12    Apt testing on Debian 12 (2GB RAM)

Tips:
  - Dev VM auto-starts by default
  - Test VMs are created on-demand and can be auto-destroyed
  - Set KEEP_TEST_VMS=1 to keep test VMs after apt testing
EOF
}

# Ensure we're in the vagrant directory
cd "${vagrant_dir}" || {
  echo "Error: vagrant/ directory not found" >&2
  exit 1
}

# Helper to show VM resource usage
show_resources() {
  if command -v vboxmanage &>/dev/null; then
    echo "Resource usage:"
    local total_ram=0
    while IFS= read -r line; do
      local vm_name=$(echo "$line" | cut -d'"' -f2)
      if [[ "$vm_name" == *"fu7ur3pr00f"* ]]; then
        local info=$(vboxmanage showvminfo "$vm_name" --machinereadable 2>/dev/null || true)
        local mem=$(echo "$info" | grep "^memory=" | cut -d= -f2)
        local state=$(echo "$info" | grep "^VMState=" | cut -d= -f2 | tr -d '"')
        if [[ -n "$mem" ]]; then
          printf "  %-25s %4sMB  %s\n" "$vm_name" "$mem" "$state"
          if [[ "$state" == "running" ]]; then
            total_ram=$((total_ram + mem))
          fi
        fi
      fi
    done < <(vboxmanage list vms 2>/dev/null || true)
    if [[ $total_ram -gt 0 ]]; then
      echo "  Total RAM in use: ${total_ram}MB"
    fi
  fi
}

# Main command handling
case "${1:-dev}" in
  dev|up)
    echo "Starting development VM..."
    vagrant up dev
    echo ""
    echo "✓ Development VM ready!"
    echo ""
    echo "To connect:"
    echo "  scripts/vagrant.sh ssh"
    echo "  cd /workspace && source .venv/bin/activate"
    echo "  fu7ur3pr00f"
    ;;

  test-apt)
    echo "=== Testing apt repository from GitHub Pages ==="
    echo "Repository: https://juanmanueldaza.github.io/fu7ur3pr00f"
    echo ""
    
    success=true
    for distro in ubuntu2404 debian12; do
      echo "Testing on ${distro}..."
      if vagrant up "$distro" --provision; then
        echo "✓ ${distro} passed"
        
        # Auto-cleanup unless user wants to keep
        if [[ "${KEEP_TEST_VMS:-}" != "1" ]]; then
          vagrant destroy -f "$distro"
          echo "  (VM destroyed to save resources)"
        fi
      else
        echo "✗ ${distro} failed" >&2
        success=false
      fi
      echo ""
    done
    
    if $success; then
      echo "✓ All apt tests passed!"
    else
      echo "✗ Some tests failed" >&2
      exit 1
    fi
    
    if [[ "${KEEP_TEST_VMS:-}" != "1" ]]; then
      echo ""
      echo "Tip: Set KEEP_TEST_VMS=1 to keep VMs for debugging"
    fi
    ;;

  multi|test-multi)
    echo "Testing multi-agent system..."
    
    # Ensure dev VM is running
    if ! vagrant status dev 2>/dev/null | grep -q "running"; then
      echo "Starting dev VM first..."
      vagrant up dev
    fi
    
    # Run the test
    vagrant ssh dev -c "cd /workspace && source .venv/bin/activate && python - <<'EOF'
import time
from fu7ur3pr00f.agents.specialists.orchestrator import get_orchestrator

print('Testing multi-agent orchestrator...')
orch = get_orchestrator()

# Test queries
queries = [
    'How can I improve my GitHub profile?',
    'What tech skills are trending?',
    'Find senior python jobs in SF',
    'Help me prepare for a promotion',
    'I want to build a SaaS product'
]

for q in queries:
    print(f'\\n[Query] {q}')
    specialist = orch.route(q)
    print(f'[Routed to] {specialist}')
    time.sleep(0.5)

print('\\n✓ Multi-agent routing test complete!')
EOF"
    ;;

  ssh)
    vm="${2:-dev}"
    # Security: Validate VM name against allowlist
    if ! is_valid_vm "${vm}"; then
      echo "Error: Invalid VM name '${vm}'. Valid names: ${VALID_VMS[*]}" >&2
      exit 1
    fi
    vagrant ssh "${vm}"
    ;;

  status|ps)
    vagrant status
    echo ""
    show_resources
    ;;

  halt)
    if [[ -n "${2:-}" ]]; then
      vm="$2"
      # Security: Validate VM name against allowlist
      if ! is_valid_vm "${vm}"; then
        echo "Error: Invalid VM name '${vm}'. Valid names: ${VALID_VMS[*]}" >&2
        exit 1
      fi
      echo "Stopping ${vm}..."
      vagrant halt "${vm}"
    else
      echo "Stopping all VMs..."
      vagrant halt
    fi
    echo "✓ VMs halted (run 'vagrant.sh dev' to restart)"
    ;;

  clean)
    echo "Destroying test VMs (keeping dev)..."
    for vm in ubuntu2404 debian12; do
      if vagrant status "$vm" 2>/dev/null | grep -qE "running|poweroff|saved"; then
        vagrant destroy -f "$vm"
        echo "✓ Destroyed $vm"
      fi
    done
    echo ""
    show_resources
    ;;

  destroy|destroy-all)
    read -p "Destroy ALL VMs including dev? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      vagrant destroy -f
      echo "✓ All VMs destroyed"
    else
      echo "Cancelled"
    fi
    ;;

  logs)
    vagrant ssh dev -c "cat /home/vagrant/provision.log 2>/dev/null || echo 'No provision log found'"
    ;;

  help|--help|-h)
    usage
    ;;

  *)
    echo "Unknown command: $1" >&2
    echo ""
    usage
    exit 1
    ;;
esac