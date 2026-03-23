#!/usr/bin/env bash
set -euo pipefail

package_name="${PACKAGE_NAME:-fu7ur3pr00f}"
repo_base_url="${REPO_BASE_URL:-https://juanmanueldaza.github.io/fu7ur3pr00f}"
repo_dist="${REPO_DIST:-stable}"
repo_component="${REPO_COMPONENT:-main}"
keyring_path="${KEYRING_PATH:-/usr/share/keyrings/fu7ur3pr00f-archive-keyring.gpg}"
sources_list_path="${SOURCES_LIST_PATH:-/etc/apt/sources.list.d/fu7ur3pr00f.list}"
log_path="${LOG_PATH:-/var/log/fu7ur3pr00f-vagrant-apt-smoke.log}"

mkdir -p "$(dirname "${log_path}")"

exec > >(tee "${log_path}") 2>&1

echo "Starting apt smoke test for ${package_name}"
echo "Repo: ${repo_base_url} ${repo_dist} ${repo_component}"

find /etc/apt/sources.list.d -maxdepth 1 -type f \
  \( -name '*microsoft*' -o -name '*azure*' \) -delete || true

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg

install -d -m 0755 "$(dirname "${keyring_path}")"
curl -fsSL "${repo_base_url}/fu7ur3pr00f-archive-keyring.gpg" -o "${keyring_path}"

cat > "${sources_list_path}" <<EOF
deb [arch=amd64 signed-by=${keyring_path}] ${repo_base_url} ${repo_dist} ${repo_component}
EOF

apt-get update
apt-cache policy "${package_name}"

apt-get install -y "${package_name}"
"${package_name}" --version

apt-get install --reinstall -y "${package_name}"
"${package_name}" --version

apt-get remove -y "${package_name}"
apt-get purge -y "${package_name}"

hash -r

if [[ -x "/usr/bin/${package_name}" ]]; then
  echo "/usr/bin/${package_name} still present after purge" >&2
  exit 1
fi

if [[ -e "/opt/${package_name}" ]]; then
  echo "/opt/${package_name} still present after purge" >&2
  find "/opt/${package_name}" -mindepth 1 -maxdepth 6 | sort | head -n 200 >&2
  exit 1
fi

if command -v "${package_name}" >/dev/null 2>&1; then
  echo "${package_name} still resolves in PATH after purge" >&2
  command -v "${package_name}" >&2
  exit 1
fi

echo "Apt smoke test completed successfully."
