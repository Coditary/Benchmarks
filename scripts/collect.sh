#!/usr/bin/env bash
# Collects all paths with metadata and passes them to the Python aggregator.

# Find all folders containing a metadata.json
TARGETS=$(find benchmarks -name "metadata.json" -printf "%h\n" | tr '\n' ' ')

# Pass all paths as arguments to the python script
python3 scripts/collect.py $TARGETS
