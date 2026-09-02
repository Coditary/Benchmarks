#!/usr/bin/env bash
set -euo pipefail
"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../../rust/install-rust.sh"
if ! command -v protoc >/dev/null 2>&1; then
  echo "protoc is required for protobuf benchmarks" >&2
  exit 1
fi
