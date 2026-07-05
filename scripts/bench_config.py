#!/usr/bin/env python3
"""Shared helpers for reading task config.json files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_BENCHMARK = {
    "warmup": 3,
    "min_runs": 10,
    "max_runs": 100,
    "runs": None,
}


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_benchmark_settings(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    benchmark = {**DEFAULT_BENCHMARK, **config.get("benchmark", {})}
    return benchmark


def get_sizes(config_path: str | Path) -> list[Any]:
    config = load_config(config_path)
    return config.get("parameters", {}).get("sizes", [])


def hyperfine_args(config_path: str | Path) -> list[str]:
    """Build hyperfine CLI flags from task config."""
    settings = get_benchmark_settings(config_path)
    args = [f"--warmup={settings['warmup']}"]

    runs = settings.get("runs")
    if runs is not None:
        args.append(f"--runs={runs}")
    else:
        args.append(f"--min-runs={settings['min_runs']}")
        args.append(f"--max-runs={settings['max_runs']}")

    return args


def sizes_csv(config_path: str | Path) -> str:
    return ",".join(str(size) for size in get_sizes(config_path))


def main() -> None:
    import sys

    if len(sys.argv) < 3:
        print("Usage: bench_config.py <command> <config.json>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    config_path = sys.argv[2]
    settings = get_benchmark_settings(config_path)

    if command == "sizes":
        print(sizes_csv(config_path))
    elif command == "hyperfine-args":
        for arg in hyperfine_args(config_path):
            print(arg)
    elif command == "get":
        if len(sys.argv) != 4:
            print("Usage: bench_config.py get <config.json> <key>", file=sys.stderr)
            sys.exit(1)
        key = sys.argv[3]
        value = settings.get(key, "")
        print(value if value is not None else "")
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
