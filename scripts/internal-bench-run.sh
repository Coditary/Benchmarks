#!/usr/bin/env bash
# Runs in-process benchmarks where the binary times only the hot path.
# Loading/parsing happens once per invocation and is excluded from timing.
set -euo pipefail

COMMAND=$1
CONFIG="../../config.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$CONFIG" ]; then
    echo "Error: config.json not found at $CONFIG" >&2
    exit 1
fi

SIZES=$("$SCRIPT_DIR/bench_config.py" sizes "$CONFIG")
SETTINGS=$("$SCRIPT_DIR/bench_config.py" export-internal-env "$CONFIG")

if [ "${CI:-}" = "true" ]; then
    "$SCRIPT_DIR/bench_config.py" describe-ci "$CONFIG" >&2
    "$SCRIPT_DIR/bench_config.py" write-ci-metadata "$CONFIG" artifacts
fi

if [ -z "$SIZES" ]; then
    echo "Error: no benchmark sizes configured for this environment." >&2
    exit 1
fi

echo "-> Running internal timing benchmark..."
mkdir -p artifacts

export $(echo "$SETTINGS" | xargs)

python3 - "$COMMAND" "$SIZES" <<'PY'
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

command_template, sizes_csv = sys.argv[1], sys.argv[2]
sizes = [size for size in sizes_csv.split(",") if size]
rows = []

for size in sizes:
    command = command_template.replace("{size}", size)
    print(f"   dataset={size}", flush=True)
    result = subprocess.run(
        command,
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    metrics = json.loads(result.stdout.strip().splitlines()[-1])
    rows.append(
        {
            "parameter_size": size,
            "mean": metrics["mean_seconds"],
            "stddev": metrics["stddev_seconds"],
            "median": metrics["median_seconds"],
            "min": metrics["min_seconds"],
            "max": metrics["max_seconds"],
            "runs": metrics["runs"],
            "load_seconds": metrics.get("load_seconds"),
            "output_bytes": metrics.get("output_bytes"),
            "output_gzip_bytes": metrics.get("output_gzip_bytes"),
            "peak_memory_bytes": metrics.get("peak_memory_bytes"),
            "cv_percent": metrics.get("cv_percent"),
            "spread_percent": metrics.get("spread_percent"),
            "load_serialize_ratio": metrics.get("load_serialize_ratio"),
            "input_bytes": metrics.get("input_bytes"),
            "load_deserialize_ratio": metrics.get("load_deserialize_ratio"),
        }
    )

out = Path("artifacts/results.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "parameter_size",
            "mean",
            "stddev",
            "median",
            "min",
            "max",
            "runs",
            "load_seconds",
            "output_bytes",
            "output_gzip_bytes",
            "peak_memory_bytes",
            "cv_percent",
            "spread_percent",
            "load_serialize_ratio",
            "input_bytes",
            "load_deserialize_ratio",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

meta = {
    "timing": "internal",
    "rows": rows,
}
Path("artifacts/timing.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
PY

"$SCRIPT_DIR/memory-run.sh" "$COMMAND"
