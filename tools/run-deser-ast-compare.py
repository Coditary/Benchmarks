#!/usr/bin/env python3
"""Compare deserialization performance: ast vs flat domains across Rust formats."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tools" / "target" / "deser-ast-compare"
TIER = "1000"
SPECS = (f"logs/{TIER}", f"profile/{TIER}", f"ast/{TIER}")

BENCHES: list[tuple[str, Path]] = [
    ("serde-json", ROOT / "benchmarks/deserialization/json/rust/serde-json"),
    ("simd-json", ROOT / "benchmarks/deserialization/json/rust/simd-json"),
    ("bitcode", ROOT / "benchmarks/deserialization/bitcode/rust/bitcode"),
    ("rkyv", ROOT / "benchmarks/deserialization/rkyv/rust/rkyv"),
    ("flexbuffers", ROOT / "benchmarks/deserialization/flexbuffers/rust/flexbuffers"),
    ("messagepack", ROOT / "benchmarks/deserialization/messagepack/rust/rmp-serde"),
    ("cbor", ROOT / "benchmarks/deserialization/cbor/rust/ciborium"),
    ("bson", ROOT / "benchmarks/deserialization/bson/rust/bson"),
    ("yaml", ROOT / "benchmarks/deserialization/yaml/rust/serde-yaml"),
    ("toml", ROOT / "benchmarks/deserialization/toml/rust/toml"),
    ("json5", ROOT / "benchmarks/deserialization/json5/rust/json5"),
    ("hjson", ROOT / "benchmarks/deserialization/hjson/rust/hjson"),
    ("cjson", ROOT / "benchmarks/deserialization/cjson/rust/cjson"),
    ("plist", ROOT / "benchmarks/deserialization/plist/rust/plist"),
    ("kdl", ROOT / "benchmarks/deserialization/kdl/rust/kdl"),
    ("xml", ROOT / "benchmarks/deserialization/xml/rust/quick-xml"),
    ("ucl", ROOT / "benchmarks/deserialization/ucl/rust/ucl"),
    ("protobuf", ROOT / "benchmarks/deserialization/protobuf/rust/prost"),
    ("capnp", ROOT / "benchmarks/deserialization/capnp/rust/capnp"),
    ("flatbuffers", ROOT / "benchmarks/deserialization/flatbuffers/rust/flatbuffers"),
]


def package_name(manifest: Path) -> str:
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.startswith("name = "):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError(f"no package name in {manifest}")


def build(crate_dir: Path) -> Path:
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(TARGET)
    subprocess.run(
        ["cargo", "build", "--release", "--manifest-path", str(crate_dir / "Cargo.toml")],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    name = package_name(crate_dir / "Cargo.toml")
    binary = TARGET / "release" / name.replace("_", "-")
    if not binary.exists():
        binary = TARGET / "release" / name
    if not binary.exists():
        raise FileNotFoundError(f"binary not found for {crate_dir}")
    return binary


def run(binary: Path, spec: str) -> dict:
    out = subprocess.check_output([str(binary), spec], cwd=ROOT, text=True)
    return json.loads(out)


def main() -> int:
    rows: list[dict] = []
    failures: list[str] = []

    for label, crate_dir in BENCHES:
        try:
            binary = build(crate_dir)
        except subprocess.CalledProcessError as error:
            failures.append(f"{label}: build failed")
            continue

        record: dict = {"format": label}
        ok = True
        for spec in SPECS:
            try:
                data = run(binary, spec)
                record[spec] = data["mean_seconds"] * 1000
                record[f"{spec}:wire"] = data["output_bytes"]
            except subprocess.CalledProcessError:
                ok = False
                failures.append(f"{label}/{spec}: run failed")
                break
        if ok:
            rows.append(record)

    print(f"Tier: {TIER}\n")
    print(f"{'format':<14} {'logs ms':>10} {'profile ms':>11} {'ast ms':>10} {'ast/logs':>9} {'ast/profile':>12}")
    print("-" * 72)
    for row in sorted(rows, key=lambda item: item.get(f"ast/{TIER}", 0), reverse=True):
        logs = row[f"logs/{TIER}"]
        profile = row[f"profile/{TIER}"]
        ast = row[f"ast/{TIER}"]
        print(
            f"{row['format']:<14} {logs:10.3f} {profile:11.3f} {ast:10.3f} "
            f"{ast / logs:9.2f}x {ast / profile:12.2f}x"
        )

    if failures:
        print("\nSkipped/failed:")
        for item in failures:
            print(f"  - {item}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
