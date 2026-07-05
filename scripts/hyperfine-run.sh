#!/usr/bin/env bash
# Runs performance benchmarks using hyperfine.
COMMAND=$1
CONFIG="../../config.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$CONFIG" ]; then
    echo "Error: config.json not found at $CONFIG" >&2
    exit 1
fi

SIZES=$("$SCRIPT_DIR/bench_config.py" sizes "$CONFIG")
mapfile -t HF_ARGS < <("$SCRIPT_DIR/bench_config.py" hyperfine-args "$CONFIG")

echo "-> Running performance benchmark..."
mkdir -p artifacts
hyperfine "${HF_ARGS[@]}" \
  --parameter-list size "$SIZES" \
  --export-csv artifacts/results.csv \
  "$COMMAND"

"$SCRIPT_DIR/memory-run.sh" "$COMMAND"
