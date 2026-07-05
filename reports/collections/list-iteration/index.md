# collections / list-iteration

Generated at 2026-07-05T23:33:13.789096+00:00

## Static metric winners

| Metric | Winner | Value |
| --- | --- | --- |
| Lines of code | C/simple-loop | 9 |
| Artifact size | Python/simple-loop | 194 bytes |
| Build time | C/simple-loop | 41.2000 ms |

## Runtime winners (mean)

| Size | Winner | Mean |
| --- | --- | --- |
| 10 | C/simple-loop | 0.5023 ms |
| 1000 | C/simple-loop | 0.5141 ms |
| 10000 | C/simple-loop | 0.5652 ms |
| 100000 | C/simple-loop | 0.9090 ms |
| 1000000 | C/simple-loop | 1.9755 ms |
| 10000000 | C/simple-loop | 11.7837 ms |
| 100000000 | C/simple-loop | 115.2762 ms |

## Memory winners (peak RSS)

| Size | Winner | Peak memory |
| --- | --- | --- |
| 10 | C/simple-loop | 3,485,696 bytes |
| 1000 | C/simple-loop | 3,485,696 bytes |
| 10000 | C/simple-loop | 3,432,448 bytes |
| 100000 | C/simple-loop | 3,424,256 bytes |
| 1000000 | C/simple-loop | 9,383,936 bytes |
| 10000000 | C/simple-loop | 81,383,424 bytes |
| 100000000 | C/simple-loop | 801,284,096 bytes |

## Full comparison

| Implementation | LoC | Artifact | Build time | Size | Mean | Peak memory |
| --- | --- | --- | --- | --- | --- | --- |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 10 | 0.5023 ms | 3,485,696 bytes |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 1000 | 0.5141 ms | 3,485,696 bytes |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 10000 | 0.5652 ms | 3,432,448 bytes |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 100000 | 0.9090 ms | 3,424,256 bytes |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 1000000 | 1.9755 ms | 9,383,936 bytes |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 10000000 | 11.7837 ms | 81,383,424 bytes |
| C/simple-loop | 9 | 14,472 bytes | 41.2000 ms | 100000000 | 115.2762 ms | 801,284,096 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 10 | 15.8675 ms | 10,522,624 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 1000 | 15.9435 ms | 10,661,888 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 10000 | 16.4635 ms | 10,915,840 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 100000 | 21.4413 ms | 14,438,400 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 1000000 | 71.0643 ms | 50,597,888 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 10000000 | 543.2732 ms | 411,701,248 bytes |
| Python/simple-loop | 9 | 194 bytes | 0.0000 ms | 100000000 | 5301.8299 ms | 4,023,291,904 bytes |

## Implementation details

### C/simple-loop

- Git hash: `624e501`
- Recorded at: `2026-07-05 23:32:09`
- Notes: Minimal C: heap int64 array, fill + sum loop. Built with gcc -O3 -s.
- CPU: AMD EPYC 7763 64-Core Processor
- OS: Linux 6.17.0-1018-azure
- RAM total: 15.62 GB
- RAM available at start: 14.11 GB
- RAM usage at start: 9.6%
- Load avg (1 min): 0.5864
- CPU governor: unknown
- CI run: True
- Source report: `benchmarks/collections/list-iteration/c/simple-loop/artifacts/report.json`

### Python/simple-loop

- Git hash: `624e501`
- Recorded at: `2026-07-05 23:33:13`
- Notes: Standard Python for-loop iteration. Script-based execution without pre-compilation.
- CPU: AMD EPYC 7763 64-Core Processor
- OS: Linux 6.17.0-1018-azure
- RAM total: 15.62 GB
- RAM available at start: 13.75 GB
- RAM usage at start: 12.0%
- Load avg (1 min): 0.8496
- CPU governor: unknown
- CI run: True
- Source report: `benchmarks/collections/list-iteration/python/simple-loop/artifacts/report.json`
