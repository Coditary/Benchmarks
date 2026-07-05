#!/usr/bin/env bash
# Runs benchmarks for a list of changed targets (CI entry point).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGETS_FILE="${1:-}"
if [ -z "$TARGETS_FILE" ] || [ ! -f "$TARGETS_FILE" ]; then
    echo "Usage: ci-run.sh <targets-file>" >&2
    exit 1
fi

if [ ! -s "$TARGETS_FILE" ]; then
    echo "No benchmark targets to run."
    exit 0
fi

export CI=true

while IFS= read -r target; do
    [ -z "$target" ] && continue
    if [ ! -f "$target/metadata.json" ]; then
        echo "Skipping missing target: $target" >&2
        continue
    fi

    echo "=== Running benchmark: $target ==="
    ./scripts/executer/code-impl-pattern.sh run "$target"
done < "$TARGETS_FILE"

python3 scripts/generate-reports.py
