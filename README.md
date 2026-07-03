# Universal Benchmark Suite

A standardized, task-driven benchmarking suite designed to fairly compare programming languages, runtimes, data structures, and CLI tools under identical conditions.

## Architecture Philosophy

Most benchmark repositories organize code by language (e.g., /rust, /cpp). This project organizes by Domain and Task. 

When deciding on a tool or language, the question is rarely "What can Rust do?" but rather "What is the fastest way to iterate over a list in any language?" or "How does pnpm compare to npm for clean installs?".

To answer these questions with hard data, this repository strictly enforces a 4-Level Hierarchy:

```text
benchmarks/
├── <domain>/                     # LEVEL 1: Broad category (e.g., collections, strings, tooling)
│   ├── README.md                 # Auto-generated: Aggregated winners of this domain
│   │
│   └── <task>/                   # LEVEL 2: Specific problem (e.g., list-iteration, map-lookup)
│       ├── README.md             # Auto-generated: Comparison charts & tables for this task
│       ├── config.json           # Shared parameters (e.g., N=10,000,000 items)
│       │
│       └── <language>/           # LEVEL 3: Environment/Language (e.g., cpp, rust, java, js)
│           │
│           └── <impl>/           # LEVEL 4: Specific implementation (e.g., std-vector, linked-list)
│               ├── main.*        # Source code
│               ├── run.sh        # Standardized executable script
│               └── metadata.json # Tags and implementation details
```

## Tooling & Infrastructure

To ensure consistent and reproducible measurements across different ecosystems, we rely on a standardized toolchain:

* Hyperfine: The gold standard for command-line benchmarking. Used inside run.sh scripts to handle statistical averaging, warmup runs, and outlier rejection.
* Bash & Make: Used as the universal glue. The CI pipeline does not need to know how to compile C++ or run Java; it simply executes run.sh in the target directory.
* Python 3: Used for data aggregation, parsing result JSONs, and generating documentation updates.
* GitHub Actions: Handles automated, selective execution using dynamic path filtering.

## The Contract: How Benchmarks Work

Every implementation (Level 4) is an isolated sandbox. To integrate into the automated pipeline, each implementation directory must provide three things:

1. metadata.json
Describes what is being tested, including language, implementation name, and tags (e.g., cpu-bound, memory-intensive).

2. run.sh
An executable bash script that handles compilation (if necessary), runs the benchmark via Hyperfine, and outputs a standardized result.json in the same directory.

3. result.json (Generated automatically)
The standardized output format consumed by our dashboard generator containing runtime, memory usage, and timestamp.

## CI/CD & Automated Reporting

To prevent massive CI build times and unnecessary pipeline runs, this repository uses Dynamic Matrix Path Filtering:

* Selective Execution: If you modify code inside a specific implementation folder, the CI will only run that specific run.sh script.
* Global Re-runs: If you modify a task's config.json (e.g., changing the input size), the CI will re-run all implementations under that specific task.
* Data Persistence: Benchmark results are stored as JSON files to maintain historical performance data without bloating source code releases.

## How to Add a New Benchmark

1. Find or create the Domain and Task folder under /benchmarks.
2. If creating a new task, add a config.json defining the shared test parameters.
3. Create your environment folder: <language>/<implementation>/.
4. Write your source code and ensure it strictly follows the rules and input sizes defined in config.json.
5. Add a run.sh script and a metadata.json file.
6. Test locally by executing ./run.sh to verify that it generates a valid result.json.
7. Open a Pull Request. The CI will automatically detect your new folder and execute the benchmark.

## Best Practices & Rules

* No I/O in CPU benchmarks: Ensure that printing to stdout or stderr is disabled during the timed portion of a code execution.
* Respect config.json: Do not hardcode input sizes or iterations in your source code. Read them from arguments/environment variables or match them strictly.
* Use Release Builds: Always compile with maximum optimization flags (e.g., -O3 for C/C++, --release for Rust).
