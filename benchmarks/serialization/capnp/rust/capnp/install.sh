#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
"$ROOT/benchmarks/serialization/rust/install-rust.sh"
if ! command -v capnp >/dev/null 2>&1; then
  if [ -x "$ROOT/tools/bin/capnp" ]; then
    export PATH="$ROOT/tools/bin:$PATH"
  fi
fi
if ! command -v capnp >/dev/null 2>&1; then
  echo "capnp is required for capnp benchmarks" >&2
  exit 1
fi
