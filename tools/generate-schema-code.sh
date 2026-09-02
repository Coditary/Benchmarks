#!/usr/bin/env bash
# Regenerates schema-specific Rust bindings for flatbuffers and capnp.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMAS="$ROOT/datasets/shared/schemas"
FLATC="${FLATC:-$ROOT/tools/bin/flatc}"
CAPNP="${CAPNP:-$ROOT/tools/bin/capnp}"
CAPNPC_RUST="$ROOT/tools/capnpc-codegen/target/release/capnpc-rust"
FLAT_GEN="$ROOT/benchmarks/serialization/flatbuffers/rust/flatbuffers/generated"
CAPNP_GEN="$ROOT/benchmarks/serialization/capnp/rust/capnp/generated"

if ! command -v "$FLATC" >/dev/null 2>&1; then
  echo "flatc not found (set FLATC or place binary in tools/bin/flatc)" >&2
  exit 1
fi

mkdir -p "$FLAT_GEN" "$CAPNP_GEN"
"$FLATC" --rust -o "$FLAT_GEN" "$SCHEMAS/benchmark.fbs"

if command -v "$CAPNP" >/dev/null 2>&1; then
  if [[ ! -x "$CAPNPC_RUST" ]]; then
    echo "building capnpc-rust plugin..." >&2
    cargo build --release --manifest-path "$ROOT/tools/capnpc-codegen/Cargo.toml"
  fi
  PATH="$(dirname "$CAPNPC_RUST"):$PATH" \
    "$CAPNP" compile \
      -orust:"$CAPNP_GEN" \
      --src-prefix="$SCHEMAS" \
      -I "$SCHEMAS" \
      "$SCHEMAS/benchmark.capnp"
else
  echo "capnp not found (set CAPNP or place binary in tools/bin/capnp)" >&2
  exit 1
fi

echo "schema codegen complete"
