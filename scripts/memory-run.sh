#!/usr/bin/env bash
# Measures peak resident memory (RSS) for each benchmark parameter.
COMMAND=$1
CONFIG="../../config.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$CONFIG" ]; then
    echo "Error: config.json not found at $CONFIG" >&2
    exit 1
fi

if [ ! -x /usr/bin/time ]; then
    echo "Error: /usr/bin/time not found (required for memory measurement)" >&2
    exit 1
fi

SIZES=$("$SCRIPT_DIR/bench_config.py" sizes "$CONFIG")
WARMUP=$("$SCRIPT_DIR/bench_config.py" get "$CONFIG" warmup)

format_memory() {
    local bytes=$1
    python3 -c "print(f'{int(\"$bytes\"):,} bytes')"
}

echo "-> Measuring peak memory usage..."
mkdir -p artifacts
echo "parameter_size,peak_memory_bytes" > artifacts/memory.csv

IFS=',' read -ra SIZE_ARRAY <<< "$SIZES"
for size in "${SIZE_ARRAY[@]}"; do
    cmd="${COMMAND//\{size\}/$size}"

    for ((i = 0; i < WARMUP; i++)); do
        eval "$cmd" >/dev/null 2>&1 || true
    done

    peak_kb=$( { /usr/bin/time -f "%M" bash -c "$cmd"; } 2>&1 >/dev/null | tail -n 1 )
    if ! [[ "$peak_kb" =~ ^[0-9]+$ ]]; then
        echo "Error: failed to measure memory for size=$size (got: '$peak_kb')" >&2
        exit 1
    fi

    peak_bytes=$((peak_kb * 1024))
    echo "$size,$peak_bytes" >> artifacts/memory.csv
    printf "   size=%s: %s\n" "$size" "$(format_memory "$peak_bytes")"
done
