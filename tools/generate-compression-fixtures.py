#!/usr/bin/env python3
"""Generate pre-compressed fixtures for decompression benchmarks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "benchmarks" / "compression"
OUT = ROOT / "datasets" / "fixtures" / "compression"
INDEX = OUT / "index.json"
BIN = ROOT / "tools" / "bin"
DATASETS = json.loads((ROOT / "datasets" / "compression" / "index.json").read_text())[
    "datasets"
]

CODECS = [
    "zstd",
    "gzip",
    "zlib",
    "deflate",
    "lz4",
    "brotli",
    "snappy",
    "bzip2",
    "xz",
    "lzma",
]


def build_binary(codec: str) -> Path:
    crate = COMP / codec / "rust" / codec
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(ROOT / "tools" / "target" / "compression-fixtures")
    subprocess.run(
        ["cargo", "build", "--release", "--manifest-path", str(crate / "Cargo.toml")],
        cwd=ROOT,
        env=env,
        check=True,
    )
    binary = Path(env["CARGO_TARGET_DIR"]) / "release" / f"compression-{codec}"
    if not binary.exists():
        raise FileNotFoundError(binary)
    return binary


def main() -> None:
    BIN.mkdir(parents=True, exist_ok=True)
    entries = []
    failures: list[str] = []

    for codec in CODECS:
        try:
            binary = build_binary(codec)
        except subprocess.CalledProcessError as error:
            failures.append(f"{codec}: build failed ({error})")
            continue

        for spec in DATASETS:
            target = OUT / codec / spec / "fixture.bin"
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    [str(binary), "--emit-fixture", str(target), spec],
                    cwd=ROOT,
                    check=True,
                )
            except subprocess.CalledProcessError:
                failures.append(f"{codec}/{spec}")
                continue

            payload = DATASETS[spec]
            entries.append(
                {
                    "codec": codec,
                    "spec": spec,
                    "fixture_path": str(target.relative_to(ROOT)),
                    "fixture_bytes": target.stat().st_size,
                    "source_payload_bytes": payload["payload_bytes"],
                    "source_payload_sha256": payload["payload_sha256"],
                    "profile": payload["profile"],
                }
            )

    manifest = {
        "fixtures_count": len(entries),
        "codecs": CODECS,
        "fixtures": entries,
        "failures": failures,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} compression fixtures to {OUT}")
    if failures:
        print("failures:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)


if __name__ == "__main__":
    main()
