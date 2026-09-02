#!/usr/bin/env bash
# Remove repo-root Rust build caches only. Does not touch source, datasets, or tests.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

remove_if_dir() {
    local path="$1"
    if [ -d "$path" ]; then
        echo "-> Removing $path"
        rm -rf "$path"
    fi
}

remove_if_dir "$ROOT/.cargo-target"
remove_if_dir "$ROOT/tools/target"
remove_if_dir "$ROOT/tools/capnpc-codegen/target"
