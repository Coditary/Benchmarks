#!/usr/bin/env bash
# Collects benchmark artifacts into per-implementation report.json files.

if [ "$#" -gt 0 ]; then
    TARGETS=("$@")
else
    mapfile -t TARGETS < <(find benchmarks -name "metadata.json" -printf "%h\n" | sort)
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
    echo "No benchmark targets found." >&2
    exit 1
fi

python3 scripts/collect.py "${TARGETS[@]}"
