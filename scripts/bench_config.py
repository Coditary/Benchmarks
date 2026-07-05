#!/usr/bin/env python3
"""Shared helpers for reading task config.json files."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - optional outside benchmark runs
    psutil = None

DEFAULT_BENCHMARK = {
    "warmup": 3,
    "min_runs": 10,
    "max_runs": 100,
    "runs": None,
}

DEFAULT_CI = {
    "memory_budget_ratio": 0.45,
    "sizes": None,
    "benchmark": {},
}

ELEMENT_BYTES = {
    "int8": 1,
    "int16": 2,
    "int32": 4,
    "int64": 8,
    "uint8": 1,
    "uint16": 2,
    "uint32": 4,
    "uint64": 8,
    "float32": 4,
    "float64": 8,
}


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_ci() -> bool:
    return os.getenv("CI") == "true"


def get_ci_settings(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    return {**DEFAULT_CI, **config.get("ci", {})}


def bytes_per_element(element_type: str) -> int:
    return ELEMENT_BYTES.get(element_type, 8)


def get_benchmark_settings(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    benchmark = {**DEFAULT_BENCHMARK, **config.get("benchmark", {})}

    if is_ci():
        ci_benchmark = get_ci_settings(config_path).get("benchmark", {})
        benchmark = {**benchmark, **ci_benchmark}

    return benchmark


def _filter_sizes_by_memory(
    sizes: list[Any],
    element_type: str,
    budget_ratio: float,
) -> tuple[list[Any], list[Any]]:
    if psutil is None:
        return sizes, []

    budget = psutil.virtual_memory().available * budget_ratio
    per_element = bytes_per_element(element_type)
    kept: list[Any] = []
    skipped: list[Any] = []

    for size in sizes:
        needed = int(size) * per_element
        if needed <= budget:
            kept.append(size)
        else:
            skipped.append(size)

    if not kept and sizes:
        smallest = min(sizes, key=lambda value: int(value))
        kept = [smallest]
        if smallest in skipped:
            skipped.remove(smallest)

    return kept, skipped


def get_effective_sizes(config_path: str | Path) -> list[Any]:
    config = load_config(config_path)
    sizes = list(config.get("parameters", {}).get("sizes", []))
    element_type = config.get("parameters", {}).get("element_type", "int64")

    if not is_ci():
        return sizes

    ci = get_ci_settings(config_path)
    explicit_sizes = ci.get("sizes")
    if explicit_sizes:
        return list(explicit_sizes)

    ratio = float(ci.get("memory_budget_ratio", DEFAULT_CI["memory_budget_ratio"]))
    return _filter_sizes_by_memory(sizes, element_type, ratio)[0]


def get_skipped_sizes(config_path: str | Path) -> list[Any]:
    config = load_config(config_path)
    sizes = list(config.get("parameters", {}).get("sizes", []))
    element_type = config.get("parameters", {}).get("element_type", "int64")

    if not is_ci():
        return []

    ci = get_ci_settings(config_path)
    explicit_sizes = ci.get("sizes")
    if explicit_sizes:
        explicit = {str(size) for size in explicit_sizes}
        return [size for size in sizes if str(size) not in explicit]

    ratio = float(ci.get("memory_budget_ratio", DEFAULT_CI["memory_budget_ratio"]))
    return _filter_sizes_by_memory(sizes, element_type, ratio)[1]


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
    return ",".join(str(size) for size in get_effective_sizes(config_path))


def describe_ci_limits(config_path: str | Path) -> str:
    if not is_ci():
        return "CI limits: not active (local run)"

    config = load_config(config_path)
    ci = get_ci_settings(config_path)
    effective = get_effective_sizes(config_path)
    skipped = get_skipped_sizes(config_path)
    lines = [
        "CI limits: active",
        f"  effective sizes: {', '.join(str(size) for size in effective)}",
    ]

    if skipped:
        lines.append(f"  skipped sizes: {', '.join(str(size) for size in skipped)}")

    if psutil is not None:
        mem = psutil.virtual_memory()
        ratio = float(ci.get("memory_budget_ratio", DEFAULT_CI["memory_budget_ratio"]))
        budget = int(mem.available * ratio)
        element_type = config.get("parameters", {}).get("element_type", "int64")
        lines.append(f"  memory budget: {budget:,} bytes ({ratio:.0%} of available RAM)")
        lines.append(f"  element size: {bytes_per_element(element_type)} bytes ({element_type})")

    benchmark = get_benchmark_settings(config_path)
    lines.append(
        "  benchmark: "
        f"warmup={benchmark['warmup']}, "
        f"runs={benchmark.get('runs')}, "
        f"min_runs={benchmark['min_runs']}, "
        f"max_runs={benchmark['max_runs']}"
    )
    return "\n".join(lines)


def write_ci_metadata(config_path: str | Path, artifacts_dir: str | Path) -> None:
    if not is_ci():
        return

    path = Path(artifacts_dir)
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "effective_sizes": get_effective_sizes(config_path),
        "skipped_sizes": get_skipped_sizes(config_path),
        "limits": describe_ci_limits(config_path),
    }
    (path / "ci_limits.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
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
    elif command == "describe-ci":
        print(describe_ci_limits(config_path))
    elif command == "write-ci-metadata":
        artifacts_dir = sys.argv[3] if len(sys.argv) > 3 else "artifacts"
        write_ci_metadata(config_path, artifacts_dir)
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
