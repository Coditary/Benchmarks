import csv
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_config import get_benchmark_settings, load_config


def get_system_info():
    """Gathers detailed hardware context, distinguishing cores and threads."""
    cpu_model = "unknown"
    physical_cores = 0
    logical_threads = 0

    mem = psutil.virtual_memory()

    governor = "unknown"
    if os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"):
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
            governor = f.read().strip()

    load_avg = os.getloadavg()[0]

    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "model name" in line:
                    cpu_model = line.split(":")[1].strip()
                    break

            logical_threads = len([line for line in lines if "processor" in line])

            core_ids = set()
            for line in lines:
                if "core id" in line:
                    core_ids.add(line.split(":")[1].strip())
            physical_cores = len(core_ids)
            if physical_cores == 0:
                physical_cores = logical_threads // 2

    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_model": cpu_model,
        "physical_cores": physical_cores,
        "logical_threads": logical_threads,
        "total_ram_bytes": mem.total,
        "available_ram_bytes": mem.available,
        "used_ram_bytes": mem.used,
        "ram_usage_percent": round(mem.percent, 2),
        "cpu_governor": governor,
        "system_load_1min": round(load_avg, 4),
        "is_ci": os.getenv("CI") == "true",
        "runner_name": os.getenv("RUNNER_NAME", "local"),
    }


def parse_benchmark_path(dir_path: str) -> tuple[str, str, str, str]:
    parts = Path(dir_path).parts
    try:
        idx = parts.index("benchmarks")
        return parts[idx + 1], parts[idx + 2], parts[idx + 3], parts[idx + 4]
    except (ValueError, IndexError):
        return "unknown", "unknown", "unknown", "unknown"


def task_config_path(dir_path: str) -> Path:
    return Path(dir_path).parent.parent / "config.json"


def get_git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode("ascii").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def collect_target(dir_path: str, git_hash: str) -> dict:
    meta_path = os.path.join(dir_path, "metadata.json")
    artifacts_dir = os.path.join(dir_path, "artifacts")
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    csv_path = os.path.join(artifacts_dir, "results.csv")
    memory_path = os.path.join(artifacts_dir, "memory.csv")
    config_path = task_config_path(dir_path)

    with open(meta_path, "r", encoding="utf-8") as handle:
        meta = json.load(handle)

    task_config = {}
    benchmark_settings = {}
    if config_path.exists():
        task_config = load_config(config_path)
        benchmark_settings = get_benchmark_settings(config_path)

    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as handle:
            metrics = json.load(handle)

    memory_by_param = {}
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                memory_by_param[row["parameter_size"]] = {
                    "peak_memory_bytes": int(row["peak_memory_bytes"]),
                }

    hyperfine_data = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                param = row.get("parameter_size", "")
                entry = dict(row)
                if param in memory_by_param:
                    entry.update(memory_by_param[param])
                if entry.get("mean"):
                    entry["mean_ms"] = round(float(entry["mean"]) * 1000, 4)
                hyperfine_data.append(entry)

    domain, test, lang, impl = parse_benchmark_path(dir_path)

    return {
        "domain": domain,
        "test": test,
        "lang": lang,
        "impl": impl,
        "language": meta.get("language", lang),
        "implementation": meta.get("implementation", impl),
        "git_hash": git_hash,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "tags": meta.get("tags", []),
        "notes": meta.get("notes", ""),
        "task_config": {
            "parameters": task_config.get("parameters", {}),
            "benchmark": benchmark_settings,
        },
        "env": get_system_info(),
        "metrics": {
            "lines_of_code": metrics.get("lines_of_code", 0),
            "artifact_size_bytes": metrics.get("artifact_size_bytes", 0),
            "build_time_ms": round(metrics.get("build_time_seconds", 0) * 1000, 4),
            "hyperfine_results": hyperfine_data,
        },
    }


def collect_data(target_dirs):
    git_hash = get_git_hash()
    written = []

    for dir_path in target_dirs:
        report = collect_target(dir_path, git_hash)
        artifacts_dir = os.path.join(dir_path, "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        report_path = os.path.join(artifacts_dir, "report.json")

        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

        written.append(report_path)
        print(f"✔ Wrote {report_path}")

    return written


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: collect.py <benchmark-dir> [<benchmark-dir> ...]", file=sys.stderr)
        sys.exit(1)

    collect_data(sys.argv[1:])
