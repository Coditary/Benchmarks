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

`benchmark` settings are passed directly to Hyperfine:

- `warmup`: warmup runs before measuring
- `min_runs` / `max_runs`: adaptive run count (default)
- `runs`: fixed run count; when set, overrides `min_runs` / `max_runs`

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

Open `reports/index.html` for the overview or `reports/<domain>/<task>/index.html` for interactive charts with language/implementation toggles.

## CI workflow

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

- Hyperfine: runtime benchmarking
- GNU `time`: peak memory measurement
- Python 3 + psutil: aggregation and report generation
- GitHub Actions: selective CI and results publishing
