#!/usr/bin/env bash
# Installs the Ubuntu toolchain required to build the C benchmark (gcc, make).
set -euo pipefail

REQUIRED_CMDS=(gcc make)
UBUNTU_PACKAGES=(build-essential)

log() {
    echo "$@" >&2
}

missing_commands() {
    local cmd
    local missing=()

    for cmd in "${REQUIRED_CMDS[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done

    if [ "${#missing[@]}" -gt 0 ]; then
        printf '%s\n' "${missing[@]}"
    fi
}

is_debian_like() {
    [ -f /etc/os-release ] || return 1
    # shellcheck source=/dev/null
    . /etc/os-release
    [[ "${ID:-}" == "ubuntu" || "${ID:-}" == "debian" ]]
}

install_on_ubuntu() {
    if ! command -v apt-get >/dev/null 2>&1; then
        log "Error: apt-get not found. Install manually: ${UBUNTU_PACKAGES[*]}"
        exit 1
    fi

    log "-> Installing Ubuntu packages: ${UBUNTU_PACKAGES[*]}"
    log "   Provides: gcc, g++, make, and standard build headers/libs"

    if [ "$(id -u)" -eq 0 ]; then
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y "${UBUNTU_PACKAGES[@]}"
    elif command -v sudo >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${UBUNTU_PACKAGES[@]}"
    else
        log "Error: root or sudo required to install packages on Ubuntu."
        log "Run: sudo apt-get update && sudo apt-get install -y build-essential"
        exit 1
    fi
}

print_manual_instructions() {
    log "Required commands: ${REQUIRED_CMDS[*]}"
    log ""
    log "Ubuntu / Debian:"
    log "  sudo apt-get update"
    log "  sudo apt-get install -y build-essential"
    log ""
    log "Fedora:"
    log "  sudo dnf install gcc make"
}

main() {
    local missing

    if [ -z "$(missing_commands)" ]; then
        log "✔ C toolchain ready (gcc, make)"
        exit 0
    fi

    missing="$(missing_commands | tr '\n' ' ')"
    log "Missing commands: ${missing% }"
    log "Ubuntu package: build-essential"

    if is_debian_like; then
        install_on_ubuntu
    else
        print_manual_instructions
        exit 1
    fi

    if [ -n "$(missing_commands)" ]; then
        log "Error: installation finished but toolchain is still incomplete."
        exit 1
    fi

    log "✔ C toolchain installed (gcc, make)"
}

main "$@"
