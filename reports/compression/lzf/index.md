# compression / lzf

Generated at 2026-09-02T23:36:00.226497+00:00

## Runtime leaderboard

Implementations ranked fastest-first per domain and tier. `vs best` shows how much slower the entry is compared to the winner.

## Output size leaderboard

Smallest raw output; lower is better.

## Gzip size leaderboard

Smallest gzip-compressed output; lower is better.

## Serialize peak RSS leaderboard

Lowest RSS during timed serialize loop; lower is better.

## Process peak RSS leaderboard

Lowest whole-process RSS (includes load); lower is better.

## Stability (CV) leaderboard

Lowest coefficient of variation (stddev/mean); lower is better.

## Spread leaderboard

Lowest min-max spread relative to mean; lower is better.

## Load/serialize ratio leaderboard

Lowest load time relative to serialize mean; lower is better.

## Static metric winners

| Metric | Winner | Value |
| --- | --- | --- |
| Lines of code | Rust/lzf | 28 |
| Artifact size | C++/liblzf | 0 bytes |
| Build time | Rust/lzf | 38.1000 ms |

## Metric winners (summary)

| Metric | Domain | Tier | Winner | Value |
| --- | --- | --- | --- | --- |

## Per-implementation results

| Implementation | Domain | Tier | Mean | Output | Gzip | Serialize RSS | Process RSS | CV% | Load/ser |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |

## Implementation details

### C++/liblzf

- Git hash: `db73122`
- Recorded at: `2026-09-02 23:29:18`
- Notes: Loads payload.bin once (untimed), then measures lzf compression.
- CPU: AMD EPYC 9V74 80-Core Processor
- OS: Linux 6.17.0-1022-azure
- RAM total: 15.62 GB
- RAM available at start: 14.59 GB
- RAM usage at start: 6.6%
- Load avg (1 min): 1.7476
- CPU governor: unknown
- CI run: True
- Source report: `benchmarks/compression/lzf/cpp/liblzf/artifacts/report.json`

### Rust/lzf

- Git hash: `db73122`
- Recorded at: `2026-09-02 23:29:33`
- Notes: Loads payload.bin once (untimed), then measures compression only.
- CPU: AMD EPYC 9V74 80-Core Processor
- OS: Linux 6.17.0-1022-azure
- RAM total: 15.62 GB
- RAM available at start: 14.61 GB
- RAM usage at start: 6.5%
- Load avg (1 min): 1.9204
- CPU governor: unknown
- CI run: True
- Source report: `benchmarks/compression/lzf/rust/lzf/artifacts/report.json`
