# Vagrant Development & Testing

Quick reference for using Vagrant with fu7ur3pr00f. Vagrant provides:
- **Dev VM** for development with synced code and data
- **Test VMs** for validating apt installation from the published GitHub Pages repository

## Prerequisites

- [Vagrant](https://www.vagrantup.com/download) 2.4+
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (or other Vagrant provider)

## Quick Start

### Development

```bash
# Start the development VM (auto-starts)
scripts/vagrant.sh dev

# SSH into the dev VM
scripts/vagrant.sh ssh

# Inside the VM:
cd /workspace
source .venv/bin/activate
fu7ur3pr00f
```

The dev VM has:
- Ubuntu 24.04
- Python 3.13 pre-installed
- Your code synced at `/workspace`
- Your secrets/config synced at `/home/vagrant/.fu7ur3pr00f`
- All dependencies pre-installed

### Testing Apt Installation

Test that your package installs correctly from the published apt repository:

```bash
# Test on both Ubuntu 24.04 and Debian 12
scripts/vagrant.sh test-apt

# Keep test VMs for debugging (normally auto-cleaned)
KEEP_TEST_VMS=1 scripts/vagrant.sh test-apt
```

This:
1. Creates clean VMs (no synced folders)
2. Adds the real GitHub Pages apt repo: `https://juanmanueldaza.github.io/fu7ur3pr00f`
3. Installs from apt as a real user would
4. Verifies the installation works
5. Auto-destroys VMs (unless `KEEP_TEST_VMS=1`)

### Multi-Agent Testing

Test the multi-agent system in the dev VM:

```bash
scripts/vagrant.sh multi
```

This starts the dev VM and runs routing tests on all 5 specialists.

## Commands

| Command | Description |
|---------|-------------|
| `vagrant.sh dev` | Start development VM |
| `vagrant.sh test-apt` | Test apt repo installation |
| `vagrant.sh multi` | Test multi-agent routing |
| `vagrant.sh ssh [VM]` | SSH into VM (default: dev) |
| `vagrant.sh status` | Show all VMs and resource usage |
| `vagrant.sh halt [VM]` | Stop VM(s) to save RAM |
| `vagrant.sh clean` | Destroy test VMs (keeps dev) |
| `vagrant.sh destroy` | Destroy ALL VMs |
| `vagrant.sh logs` | Show dev VM provision logs |

## VMs

### `dev` — Development

- **OS:** Ubuntu 24.04
- **RAM:** 4GB
- **CPUs:** 2
- **Synced folders:** Yes (code + data)
- **Use case:** Active development, testing, iteration

```bash
scripts/vagrant.sh dev
scripts/vagrant.sh ssh
cd /workspace && source .venv/bin/activate && fu7ur3pr00f
```

### `ubuntu2404` — Apt Testing (Ubuntu)

- **OS:** Ubuntu 24.04
- **RAM:** 2GB (minimal)
- **CPUs:** 1
- **Synced folders:** No (clean environment)
- **Use case:** Test real apt installation from GitHub Pages
- **Auto-cleanup:** Yes (unless `KEEP_TEST_VMS=1`)

```bash
scripts/vagrant.sh test-apt
```

### `debian12` — Apt Testing (Debian)

- **OS:** Debian 12 (Bookworm)
- **RAM:** 2GB (minimal)
- **CPUs:** 1
- **Synced folders:** No (clean environment)
- **Use case:** Test real apt installation from GitHub Pages
- **Auto-cleanup:** Yes (unless `KEEP_TEST_VMS=1`)

```bash
scripts/vagrant.sh test-apt
```

## Resource Management

Each VM uses RAM. To see current usage:

```bash
scripts/vagrant.sh status
```

Output shows which VMs are running and how much RAM they're using. To save resources:

```bash
# Stop all VMs (keeps state, fast to restart)
scripts/vagrant.sh halt

# Stop only test VMs
scripts/vagrant.sh clean

# Destroy test VMs completely
scripts/vagrant.sh clean
```

## Workflow Examples

### Local Development

```bash
# Boot dev VM once at start of day
scripts/vagrant.sh dev

# Do your work
scripts/vagrant.sh ssh
cd /workspace && source .venv/bin/activate
# ... code, test, run fu7ur3pr00f ...

# Stop VM when done (saves RAM)
scripts/vagrant.sh halt dev
```

### Before Publishing Release

```bash
# Build the .deb package
scripts/build_deb.sh

# Build the apt repository
scripts/build_apt_repo.sh dist/deb/fu7ur3pr00f_*.deb

# Test real-world installation from your GitHub Pages repo
scripts/vagrant.sh test-apt

# If tests pass, deploy the repo and tag release
git tag v0.2.0
git push origin v0.2.0
```

### Multi-Agent Testing

```bash
# Test the specialist routing
scripts/vagrant.sh multi

# Or manually in dev VM
scripts/vagrant.sh ssh
cd /workspace && source .venv/bin/activate

# Start an interactive session
fu7ur3pr00f

# Then inside chat:
/agents          # List specialists
who am i?        # Coach should respond
how can i get promoted?  # Also Coach
find me a job    # Should route to Jobs specialist
```

## Troubleshooting

### "Vagrant: command not found"

Install Vagrant from https://www.vagrantup.com/download

### "VirtualBox: command not found"

Install VirtualBox from https://www.virtualbox.org/wiki/Downloads

### "VM boot timeout"

Vagrant VMs take 1-2 minutes to boot. If it times out:
```bash
# Check VirtualBox status
vboxmanage list vms

# Destroy and retry
scripts/vagrant.sh destroy
scripts/vagrant.sh dev
```

### "No module named fu7ur3pr00f"

The dev VM installs from source. If reinstalling after code changes:
```bash
scripts/vagrant.sh ssh
cd /workspace
pip install -e .
```

### "ChromaDB queries are slow"

VirtualBox synced folders can impact SQLite performance. This is expected.
Options:
1. Keep working with it (acceptable for dev)
2. Run on local machine instead (no synced folders)
3. Use Docker for testing instead

### "Test VMs keep running"

By default, test VMs are auto-destroyed after `test-apt` completes. If they're still running:
```bash
scripts/vagrant.sh clean
```

To keep them for debugging:
```bash
KEEP_TEST_VMS=1 scripts/vagrant.sh test-apt
scripts/vagrant.sh destroy ubuntu2404  # When done
```

## Advanced

### Customize VM Resources

Edit `vagrant/Vagrantfile`:

```ruby
dev.vm.provider "virtualbox" do |vb|
  vb.memory = 8192   # More RAM
  vb.cpus = 4        # More CPUs
end
```

Then reprovision:
```bash
vagrant up dev --provision
```

### Use a Different Linux Box

```bash
# Set before running vagrant
export VAGRANT_BOX="ubuntu/jammy64"
scripts/vagrant.sh dev
```

### Manual Vagrant Commands

```bash
cd vagrant

# Direct vagrant commands still work
vagrant status
vagrant up dev
vagrant ssh dev
vagrant halt
vagrant destroy
```

## Vagrant vs. Docker vs. Local

| Task | Recommended | Why |
|------|-------------|-----|
| **Development** | Local or dev VM | Fast iteration, no startup overhead |
| **Apt testing** | Vagrant test VMs | Real GitHub Pages repo, clean environment |
| **Python unit tests** | Local or CI | No isolation needed, fast |
| **Apt validation** | Docker (`validate_apt_artifact.sh`) | Lightweight, parallel testing |
| **Cross-distro testing** | Docker or Vagrant | Your choice |

## See Also

- [Main README](../README.md) — Installation, scripts, and documentation
- [Vagrant Documentation](https://www.vagrantup.com/docs)
