# Scripts Reference

All scripts are in `scripts/`. Most are bash and executable.

---

## Quick Reference

| Script | Purpose | Type |
|--------|---------|------|
| [`setup.sh`](#setupsh--one-time-configuration) | Azure/config setup | User-facing |
| [`fresh_install_check.sh`](#fresh_install_checksh--validate-pipx-installation) | Validate pipx install | User-facing |
| [`clean_dev_artifacts.sh`](#clean_dev_artifactssh--clean-build-artifacts) | Clean build artifacts | Dev |
| [`run_tests.py`](#run_testspy--test-runner) | Run test suite | Dev |
| [`setup_precommit.sh`](#setup_precommitsh--install-pre-commit-hooks) | Install pre-commit hooks | Dev |
| [`build_deb.sh`](#build_debsh--build-deb-package) | Build .deb package | CI/Build |
| [`build_apt_repo.sh`](#build_apt_reposh--build-apt-repository) | Build apt repository | CI/Build |
| [`validate_apt_artifact.sh`](#validate_apt_artifactsh--test-deb-in-containers) | Test .deb in Docker | CI/Test |
| [`vagrant.sh`](#vagrantsh--vagrant-management) | Unified Vagrant management | Dev/Test |

---

## User-Facing Scripts

### `setup.sh` — One-time configuration

Configures Azure OpenAI automatically and copies career data.

```bash
./scripts/setup.sh
```

**What it does:**
1. Checks Azure CLI login (runs device code flow if needed)
2. Finds Azure OpenAI resource in your subscription
3. Extracts API key and endpoint
4. Lists deployments and picks appropriate models
5. Writes `~/.fu7ur3pr00f/.env` with secure permissions (0600)
6. Copies career data from `data/raw/` to `~/.fu7ur3pr00f/data/raw/`
7. Tests the connection

**Requirements:**
- Azure CLI installed
- Logged in to Azure
- Azure OpenAI resource with deployments

---

### `fresh_install_check.sh` — Validate pipx installation

Tests a clean pipx install in an isolated environment.

```bash
./scripts/fresh_install_check.sh --source local --config-from .env
./scripts/fresh_install_check.sh --source pypi --config-from .env
```

**Options:**
| Option | Description |
|--------|-------------|
| `--source local` | Install from current directory (default) |
| `--source pypi` | Install from PyPI |
| `--config-from PATH` | Copy `.env` file to isolated HOME |
| `--keep` | Don't delete temp directory after test |

**What it does:**
1. Creates temp HOME directory
2. Installs fu7ur3pr00f via pipx
3. Copies glab config if present
4. Runs diagnostics module
5. Cleans up (unless `--keep`)

---

## Development Scripts

### `run_tests.py` — Test runner

Python script to run the test suite.

```bash
python scripts/run_tests.py
```

Equivalent to `pytest tests/ -q` but with additional output formatting.

---

### `setup_precommit.sh` — Install pre-commit hooks

Installs pre-commit and sets up git hooks.

```bash
./scripts/setup_precommit.sh
```

**What it does:**
1. Installs `pre-commit` via pip
2. Runs `pre-commit install` to register git hooks
3. Optionally runs `pre-commit run --all-files` to validate existing code

The pre-commit configuration in `.pre-commit-config.yaml` runs ruff lint and format checks on every commit.

---

### `clean_dev_artifacts.sh` — Clean build artifacts

Removes Python cache, build directories, and transient data.

```bash
./scripts/clean_dev_artifacts.sh
```

**What it removes:**
- `dist/`, `build/`
- `__pycache__/` directories
- `*.pyc` files
- `data/cache/` (market data cache)

---

## Build Scripts

### `build_deb.sh` — Build .deb package

Creates a self-contained Debian package with bundled Python runtime.

```bash
./scripts/build_deb.sh
```

**Environment variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `VERSION` | From `pyproject.toml` | Package version |
| `DIST_DIR` | `dist/deb` | Output directory |

**What it does:**
1. Creates build virtualenv
2. Builds wheel with hatchling
3. Downloads python-build-standalone (Python 3.13)
4. Installs wheel into bundled Python
5. Bundles github-mcp-server
6. Prunes unnecessary files (tests, pip, tcl/tk)
7. Creates wrapper script at `/usr/bin/fu7ur3pr00f`
8. Builds .deb with dpkg-deb

**Output:** `dist/deb/fu7ur3pr00f_<version>_amd64.deb`

**Requirements:** Python 3.13, `python3-venv`, `python3.13-venv`, `dpkg-deb`, `jq`, `curl`

---

### `build_apt_repo.sh` — Build apt repository

Creates a signed apt repository from a .deb package.

```bash
./scripts/build_apt_repo.sh path/to/package.deb
```

**Environment variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_DIR` | `dist/apt` | Repository output directory |
| `APT_DIST` | `stable` | Distribution name |
| `APT_COMPONENT` | `main` | Component name |
| `APT_GPG_PRIVATE_KEY` | — | GPG private key for signing |
| `APT_GPG_PASSPHRASE` | — | GPG passphrase |
| `APT_GPG_ALLOW_EPHEMERAL` | `0` | Allow temp key for testing |

**Output:**
```
dist/apt/
├── dists/stable/
│   ├── Release
│   ├── Release.gpg
│   ├── InRelease
│   └── main/binary-amd64/
├── pool/main/f/fu7ur3pr00f/
│   └── fu7ur3pr00f_<version>_amd64.deb
└── fu7ur3pr00f-archive-keyring.gpg
```

---

## Test Scripts

### `validate_apt_artifact.sh` — Test .deb in containers

Validates a .deb package installs/uninstalls cleanly in Docker containers.

```bash
./scripts/validate_apt_artifact.sh path/to/package.deb
```

**Environment variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `APT_VALIDATION_IMAGES` | `ubuntu:24.04 debian:12` | Container images to test |

**What it does:**
1. Builds temp apt repo with `build_apt_repo.sh`
2. Starts local HTTP server
3. Runs Docker container for each image
4. Tests: install → version → reinstall → version → remove → purge
5. Verifies no files remain after purge
6. Cleans up

**Requirements:** Docker, `apt-ftparchive`, `dpkg-scanpackages`, `gpg`

---

### `run_vagrant_apt_smoke.sh` — Test apt packages in VMs

---

### `vagrant.sh` — Vagrant management

Unified script to manage development and test VMs.

```bash
./scripts/vagrant.sh dev        # Start development VM
./scripts/vagrant.sh test-apt   # Test apt repo from GitHub Pages
./scripts/vagrant.sh multi      # Test multi-agent routing
./scripts/vagrant.sh ssh        # SSH into dev VM
./scripts/vagrant.sh status     # Show VM status and resource usage
./scripts/vagrant.sh halt       # Stop VM(s)
./scripts/vagrant.sh clean      # Destroy test VMs (keep dev)
./scripts/vagrant.sh destroy    # Destroy all VMs
```

**Commands:**
| Command | Description |
|---------|-------------|
| `dev` | Start development VM (default) |
| `test-apt` | Test apt repository from GitHub Pages on Ubuntu + Debian |
| `multi` | Test multi-agent routing in dev VM |
| `ssh [VM]` | SSH into VM (default: dev) |
| `status` | Show all VMs and resource usage |
| `halt [VM]` | Stop VM(s) to save RAM |
| `clean` | Destroy test VMs (keeps dev) |
| `destroy` | Destroy ALL VMs |
| `logs` | Show dev VM provisioning logs |

**VMs:**
- **dev** — Development environment (4GB RAM, synced folders)
- **ubuntu2404** — Apt test VM (2GB RAM, auto-cleaned)
- **debian12** — Apt test VM (2GB RAM, auto-cleaned)

**Environment variables:**
| Variable | Effect |
|----------|--------|
| `KEEP_TEST_VMS=1` | Keep test VMs after apt testing (normally auto-destroyed) |

**What it does:**
- **dev VM**: Ubuntu 24.04, Python 3.13, all dependencies, synced code and data
- **test-apt**: Creates clean VMs, adds your published GitHub Pages apt repo, tests installation as real user would

**Requirements:** Vagrant + VirtualBox

**See also:** `vagrant/README.md` for detailed usage guide

---

## Quick Reference by Task

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -q` or `python scripts/run_tests.py` |
| Set up pre-commit | `./scripts/setup_precommit.sh` |
| First-time Azure setup | `./scripts/setup.sh` |
| Validate pipx install | `./scripts/fresh_install_check.sh --source local --config-from .env` |
| Test apt package | `./scripts/validate_apt_artifact.sh dist/deb/fu7ur3pr00f_*.deb` |
| Dev VM | `./scripts/vagrant.sh dev` |
| Test apt repo | `./scripts/vagrant.sh test-apt` |
| Test multi-agent | `./scripts/vagrant.sh multi` |
| Build .deb | `./scripts/build_deb.sh` |
| Build apt repo | `./scripts/build_apt_repo.sh dist/deb/fu7ur3pr00f_*.deb` |
| Clean artifacts | `./scripts/clean_dev_artifacts.sh` |

---

## See Also

- [Development Guide](development.md)
- `vagrant/README.md` — Comprehensive Vagrant usage guide

