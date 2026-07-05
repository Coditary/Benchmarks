#!/usr/bin/env python3
"""Detect benchmark implementations affected by git changes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def git_changed_files(base_ref: str) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        ["git", "diff", "--name-only", base_ref, "HEAD"],
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
    ]

    for command in commands:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line for line in result.stdout.splitlines() if line.strip()]

    return []


def impl_dir_for(path: Path) -> Path | None:
    parts = path.parts
    if len(parts) < 5 or parts[0] != "benchmarks":
        return None

    candidate = Path(*parts[:5])
    if (candidate / "metadata.json").exists():
        return candidate
    return None


def task_dir_for(path: Path) -> Path | None:
    parts = path.parts
    if len(parts) < 4 or parts[0] != "benchmarks":
        return None

    if path.name == "config.json":
        return Path(*parts[:4])
    return None


def impls_for_task(task_dir: Path) -> list[Path]:
    if not task_dir.exists():
        return []
    return sorted(
        meta.parent
        for meta in task_dir.rglob("metadata.json")
        if meta.parent != task_dir
    )


def detect_targets(changed_files: list[str]) -> list[str]:
    targets: set[str] = set()
    tasks: set[Path] = set()

    for file_path in changed_files:
        path = Path(file_path)

        if path.parts[:1] == ("scripts",):
            return sorted(
                str(meta.parent)
                for meta in Path("benchmarks").rglob("metadata.json")
            )

        impl = impl_dir_for(path)
        if impl is not None:
            targets.add(str(impl))

        task = task_dir_for(path)
        if task is not None:
            tasks.add(task)

    for task in tasks:
        for impl in impls_for_task(task):
            targets.add(str(impl))

    return sorted(targets)


def main() -> None:
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    changed = git_changed_files(base_ref)
    targets = detect_targets(changed)

    for target in targets:
        print(target)


if __name__ == "__main__":
    main()
