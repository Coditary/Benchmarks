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

FAILED=()

describe_exit_code() {
    local code=$1
    case "$code" in
        137)
            echo "Process was killed with SIGKILL (exit 137). This usually means the GitHub runner ran out of memory (OOM)."
            ;;
        143)
            echo "Process was terminated with SIGTERM (exit 143). Common causes on GitHub Actions: OOM killer, job/step timeout, or the runner stopping a long benchmark."
            ;;
        124)
            echo "Process hit a timeout (exit 124)."
            ;;
        *)
            echo "Benchmark exited with code $code."
            ;;
    esac
}

while IFS= read -r target; do
    [ -z "$target" ] && continue
    if [ ! -f "$target/metadata.json" ]; then
        echo "Skipping missing target: $target" >&2
        continue
    fi

    echo "=== Running benchmark: $target ==="
    set +e
    ./scripts/executer/code-impl-pattern.sh run "$target"
    exit_code=$?
    set -e

    if [ "$exit_code" -ne 0 ]; then
        echo "::error title=Benchmark failed::${target} - $(describe_exit_code "$exit_code")" >&2
        describe_exit_code "$exit_code" >&2
        echo "Hint: check task config ci.memory_budget_ratio / ci.sizes and reduce local sizes for GitHub-hosted runners (~7 GB RAM)." >&2
        FAILED+=("$target ($exit_code)")
    fi
done < "$TARGETS_FILE"

set +e
python3 scripts/generate-reports.py
report_exit=$?
set -e

if [ "$report_exit" -ne 0 ]; then
    echo "::warning title=Report generation failed::generate-reports.py exited with $report_exit" >&2
fi

if [ "${#FAILED[@]}" -gt 0 ]; then
    echo ""
    echo "The following benchmark target(s) failed:"
    printf '  - %s\n' "${FAILED[@]}"
    exit 1
fi
