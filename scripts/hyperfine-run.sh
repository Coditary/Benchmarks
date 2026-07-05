#!/usr/bin/env bash
# Runs performance benchmarks using hyperfine.
COMMAND=$1
# We are currently in benchmarks/domain/task/lang/impl
# config.json is in ../../config.json
CONFIG="../../config.json"

if [ ! -f "$CONFIG" ]; then
    echo "Error: config.json not found at $CONFIG" >&2
    exit 1
fi

# Extract parameters from config.json
SIZES=$(python3 -c "import json; print(','.join(map(str, json.load(open('$CONFIG'))['parameters']['sizes'])))")
WARMUP=$(python3 -c "import json; print(json.load(open('$CONFIG'))['parameters'].get('warmup', 3))")

echo "-> Running performance benchmark..."
mkdir -p artifacts
hyperfine --warmup "$WARMUP" \
  --parameter-list size "$SIZES" \
  --export-csv artifacts/results.csv \
  "$COMMAND"
