#!/usr/bin/env bash
# Installs gcc on Ubuntu (build-essential).
set -euo pipefail

REQUIRED_CMDS=(gcc)
UBUNTU_PACKAGES=(build-essential)

log() { echo "$@" >&2; }

missing_commands() {
    local cmd missing=()
    for cmd in "${REQUIRED_CMDS[@]}"; do
        command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
    done
    ((${#missing[@]})) && printf '%s\n' "${missing[@]}"
}

is_debian_like() {
    [ -f /etc/os-release ] || return 1
    # shellcheck source=/dev/null
    . /etc/os-release
    [[ "${ID:-}" == "ubuntu" || "${ID:-}" == "debian" ]]
}

install_on_ubuntu() {
    log "-> Installing ${UBUNTU_PACKAGES[*]} (gcc)"
    if [ "$(id -u)" -eq 0 ]; then
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y "${UBUNTU_PACKAGES[@]}"
    else
        sudo apt-get update -qq
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${UBUNTU_PACKAGES[@]}"
    fi
}

main() {
    if [ -z "$(missing_commands || true)" ]; then
        log "✔ gcc ready"
        exit 0
    fi

    if is_debian_like; then
        install_on_ubuntu
    else
        log "Install gcc manually (Ubuntu: sudo apt install build-essential)"
        exit 1
    fi

    log "✔ gcc installed"
}

main "$@"
