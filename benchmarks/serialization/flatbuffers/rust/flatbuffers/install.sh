#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
"$ROOT/benchmarks/serialization/rust/install-rust.sh"

if ! command -v flatc >/dev/null 2>&1; then
  if [ -x "$ROOT/tools/bin/flatc" ]; then
    export PATH="$ROOT/tools/bin:$PATH"
  else
    echo "flatc not found; using committed generated flatbuffers code" >&2
  fi
fi
