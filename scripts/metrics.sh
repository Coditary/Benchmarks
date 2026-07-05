#!/usr/bin/env bash
# Computes static engineering metrics for a target implementation.
# Metrics are saved to artifacts/metrics.json.

if [ ! -f "metadata.json" ]; then
  echo "⚠ WARNING: No metadata.json found. Skipping metrics." >&2
  exit 1
fi

# Ensure artifacts directory exists
mkdir -p artifacts

# Extract metadata
SOURCES=$(python3 -c 'import json, os; print(" ".join([f for f in json.load(open("metadata.json")).get("source_files", []) if os.path.exists(f)]))')
ARTIFACT=$(python3 -c 'import json; print(json.load(open("metadata.json")).get("artifact_path", ""))')

# Count Lines of Code (LoC)
if command -v tokei &> /dev/null; then
  LOC=$(tokei $SOURCES --output json 2>/dev/null | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("Total", {}).get("code", 0))')
else
  LOC=$(cat $SOURCES | grep -v -E '^[[:space:]]*($|#|//|/\*|\*)' | wc -l)
fi

# Measure artifact size
SIZE=0
if [ -f "$ARTIFACT" ]; then
  SIZE=$(stat -c %s "$ARTIFACT" 2>/dev/null || stat -f %z "$ARTIFACT" 2>/dev/null || echo 0)
fi

# Measure build time only if a build hook exists
HAS_BUILD=$(python3 -c "import json; print(json.load(open('metadata.json')).get('hooks', {}).get('build', ''))")

if [[ -n "$HAS_BUILD" && "$HAS_BUILD" != "None" ]]; then
    START_TIME=$(date +%s.%N)
    eval "$HAS_BUILD" >/dev/null 2>&1 || true
    END_TIME=$(date +%s.%N)
    BUILD_TIME=$(python3 -c "print(round($END_TIME - $START_TIME, 4))")
else
    # No build hook defined: set time to 0.0
    BUILD_TIME=0.0
fi

# Output to artifacts/metrics.json
python3 -c "
import json
metrics = {
    'lines_of_code': int('$LOC'), 
    'artifact_size_bytes': int('$SIZE'), 
    'build_time_seconds': float('$BUILD_TIME')
}
with open('artifacts/metrics.json', 'w') as f: 
    json.dump(metrics, f, indent=2)
"

echo "✔ Metrics generated: $LOC LoC | $SIZE Bytes | ${BUILD_TIME}s Build Time"
