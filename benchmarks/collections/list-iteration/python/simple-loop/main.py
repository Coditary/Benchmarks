import json
import os
import statistics
import sys
import time


def env_int(name: str, fallback: int) -> int:
    value = os.getenv(name)
    if not value:
        return fallback
    return int(value)


def main() -> None:
    size = int(sys.argv[1])
    warmup = env_int("BENCH_WARMUP", 3)
    runs = env_int("BENCH_RUNS", 0) or env_int("BENCH_MAX_RUNS", 50)

    load_start = time.perf_counter()
    data = list(range(size))
    load_seconds = time.perf_counter() - load_start

    total = 0
    for _ in range(warmup):
        for element in data:
            total += element

    samples: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        for element in data:
            total += element
        samples.append(time.perf_counter() - start)

    payload = {
        "mean_seconds": statistics.mean(samples),
        "median_seconds": statistics.median(samples),
        "stddev_seconds": statistics.pstdev(samples) if len(samples) > 1 else 0.0,
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "runs": runs,
        "warmup": warmup,
        "load_seconds": load_seconds,
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
