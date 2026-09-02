# Universal Benchmark Suite

A standardized, task-driven benchmarking suite designed to fairly compare programming languages, runtimes, data structures, and CLI tools under identical conditions.

## Architecture

```text
benchmarks/
├── <domain>/
│   └── <task>/
│       ├── config.json          # Shared parameters + benchmark settings
│       └── <language>/
│           └── <impl>/
│               ├── main.*
│               ├── metadata.json
│               └── artifacts/   # Local results (gitignored on main)
│                   ├── results.csv
│                   ├── memory.csv
│                   ├── metrics.json
│                   └── report.json
tools/cpp/                       # Shared C++ bench-support (not a benchmark)
├── bench-support/include/bench/
└── cmake/BenchDeps.cmake
```

Results are published separately on the `benchmark-results` branch:

```text
published/benchmarks/.../artifacts/report.json
reports/<domain>/<task>/index.md
reports/<domain>/<task>/index.html
manifest.json
```

## Task configuration

Each task defines shared parameters and benchmark execution settings in `config.json`:

```json
{
  "domain": "collections",
  "task_name": "list-iteration",
  "description": "Measures iteration time across various sequence sizes.",
  "parameters": {
    "sizes": [10, 100, 1000, 100000],
    "element_type": "int64"
  },
  "benchmark": {
    "warmup": 3,
    "min_runs": 10,
    "max_runs": 100,
    "runs": null
  }
}
```

`benchmark` settings are passed to each implementation via environment variables (`BENCH_WARMUP`, `BENCH_MIN_RUNS`, `BENCH_MAX_RUNS`, `BENCH_RUNS`):

- `warmup`: untimed warmup iterations before measuring
- `min_runs` / `max_runs`: timed iteration count (default uses `max_runs`)
- `runs`: fixed timed run count; when set, overrides `min_runs` / `max_runs`

Implementations use **internal timing** by default (`"timing": "internal"` in `metadata.json`): setup/load happens once per process, only the hot path is measured in-process. Set `"timing": "hyperfine"` to opt into whole-process timing via Hyperfine.

`ci` settings apply automatically when `CI=true` (GitHub Actions):

```json
"ci": {
  "memory_budget_ratio": 0.45,
  "benchmark": {
    "warmup": 2,
    "min_runs": 5,
    "max_runs": 30
  }
}
```

- `memory_budget_ratio`: skips parameter sizes that would need more RAM than this fraction of currently available memory (based on `element_type`, e.g. `int64` = 8 bytes per element)
- `sizes`: optional explicit CI size list; when set, overrides automatic filtering
- `ci.benchmark`: lighter internal timing settings for faster, safer CI runs

Skipped CI sizes are logged in the workflow output and saved to `artifacts/ci_limits.json`.

Memory is measured separately with GNU `time` and stored as `peak_memory_bytes`.

## Local usage

Run all benchmarks:

```bash
./bench.sh run
```

Run a filtered subset:

```bash
./bench.sh run collections/list-iteration
```

Generate comparison reports locally:

```bash
./bench.sh reports
```

Generate reports only for a specific scope (incremental update):

```bash
./bench.sh reports collections/list-iteration
```

Remove compiled binaries and build caches (does not touch source code or datasets):

```bash
./bench.sh clean
```

Open `reports/index.html` for the overview or `reports/<domain>/<task>/index.html` for interactive charts with language/implementation toggles.

## Datasets

The repo keeps a **single canonical source** under `datasets/shared/` (`canonical.json` per domain/tier).
Serialization benches read it directly. Deserialization and decompression benches derive wire bytes
from it at runtime (encode/compress in the untimed load phase), so no per-format fixture copies are
stored in git.

Synthetic compression inputs (`random`, `sparse`, `english`, `repetitive`) live under
`datasets/compression/` because they are not derived from the structured canonical datasets.

Optional: materialize fixture files for inspection only:

```bash
python3 tools/generate-fixtures.py --formats serde-yaml toml quick-xml
```

## C++ benchmarks

C++ implementations live under `benchmarks/<domain>/<task>/cpp/<impl>/` and share timing helpers in `tools/cpp/bench-support/`.

| Domain | C++ implementations | Notes |
|--------|---------------------|-------|
| serialization / deserialization | `nlohmann-json`, `msgpack-cxx`, `protobuf-cpp`, `flatbuffers-cpp`, `capnp-cpp`, `flexbuffers-cpp` | Wire bytes derived from canonical JSON at runtime |
| serialization / deserialization (text) | `yaml-cpp`, `tomlplusplus`, `pugixml`, custom `ini` / `kdl` | YAML/TOML/XML via libraries; INI/KDL use shared custom wire format |
| serialization / deserialization (more) | `nlohmann` BSON/CBOR, custom `csv`/`tsv`/`ucl`, `json5-cpp`, `hjson-cpp`, `cjson`, `pugixml` plist | BSON/CBOR via nlohmann/json; CSV/TSV/UCL custom wire format |
| compression / decompression | `libzstd`, `zlib`, `lz4`, `libbz2`, `snappy`, `libbrotli`, `liblzma`, `liblzf`, `fastlz`, `minilzo`, `lzfse`, `libdeflate`, `zopfli`, `zlib-ng` | Structured domains read canonical JSON; synthetic payloads stay under `datasets/compression/` |
| Rust-only formats | — | `bitcode`, `rkyv` (no C++ equivalent) |

Install C++ dependencies (Debian/Ubuntu or Fedora):

```bash
./tools/cpp/install-cpp.sh
```

Scaffold or regenerate all C++ benchmarks:

```bash
python3 tools/scaffold-cpp-benchmarks.py
python3 tools/scaffold-text-format-benchmarks.py
python3 tools/scaffold-extra-format-benchmarks.py
python3 tools/fix-cpp-cmake.py
```

Run a single C++ target:

```bash
./scripts/executer/code-impl-pattern.sh run benchmarks/serialization/json/cpp/nlohmann-json
```

Build uses CMake (`build.sh` per implementation). nlohmann/json is fetched automatically when not installed system-wide.


GitHub Actions runs on changes under `benchmarks/**` or `scripts/**`.

Change detection rules:

- New/changed implementation folder: only that implementation is benchmarked
- Changed `config.json`: all implementations under that task are benchmarked
- Changed shared scripts: all implementations are benchmarked

On push to `main`, CI:

1. Detects affected targets with `scripts/detect-changes.py`
2. Runs only those targets via `scripts/ci-run.sh`
3. Publishes results to the `benchmark-results` branch via `scripts/publish-results.sh`
4. Regenerates markdown + interactive HTML reports on that branch

Pull requests run benchmarks but do not publish results.

## Adding a new implementation

1. Create `benchmarks/<domain>/<task>/<language>/<impl>/`
2. Add source code and `metadata.json`
3. Ensure the task has a `config.json`
4. Test locally:

```bash
./scripts/executer/code-impl-pattern.sh run benchmarks/<domain>/<task>/<language>/<impl>
```

5. Commit and push to `main`

Example target:

```text
benchmarks/collections/list-iteration/python/smart-loop/
```

Only that new folder will be benchmarked by CI unless the shared task config changed.

## Report outputs

For each task, CI generates:

- `reports/<domain>/<task>/index.md`: winner tables for runtime, memory, lines of code, artifact size, and build time
- `reports/<domain>/<task>/index.html`: interactive charts with language/implementation filters, static metric bar charts, build-time non-zero filter, comparability warnings, and expandable implementation details (git hash, notes, environment, raw per-size stats)

Each implementation also keeps its own machine-readable result file:

- `published/benchmarks/.../artifacts/report.json`

## Tooling

- Internal in-process timing: runtime benchmarking (default)
- Hyperfine: optional whole-process timing (`"timing": "hyperfine"`)
- GNU `time`: peak memory measurement
- Python 3 + psutil: aggregation and report generation
- GitHub Actions: selective CI and results publishing
