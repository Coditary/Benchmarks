# serialization / bitcode

Generated at 2026-09-02T23:36:00.302463+00:00

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
| Lines of code | Rust/bitcode | 28 |
| Artifact size | Rust/bitcode | 0 bytes |
| Build time | Rust/bitcode | 603.8000 ms |

## Metric winners (summary)

| Metric | Domain | Tier | Winner | Value |
| --- | --- | --- | --- | --- |

## Per-implementation results

| Implementation | Domain | Tier | Mean | Output | Gzip | Serialize RSS | Process RSS | CV% | Load/ser |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |

## Implementation details

### Rust/bitcode

- Git hash: `db73122`
- Recorded at: `2026-09-02 23:16:54`
- Notes: bitcode::encode on shared log dataset types.
- CPU: AMD EPYC 9V74 80-Core Processor
- OS: Linux 6.17.0-1022-azure
- RAM total: 15.62 GB
- RAM available at start: 14.43 GB
- RAM usage at start: 7.6%
- Load avg (1 min): 1.5796
- CPU governor: unknown
- CI run: True
- Source report: `benchmarks/serialization/bitcode/rust/bitcode/artifacts/report.json`
