#!/usr/bin/env python3
"""Optionally materialize wire-format fixture files for inspection or cache warming.

Benchmarks no longer require on-disk fixtures: deserialization benches derive wire
bytes from `datasets/shared/` at runtime. Use this tool only when you explicitly
want fixture files written under `datasets/fixtures/`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS_INDEX = ROOT / "datasets" / "index.json"
FIXTURES_INDEX = ROOT / "datasets" / "fixtures" / "index.json"
SERIALIZATION_CONFIG = ROOT / "benchmarks" / "serialization" / "json" / "config.json"

# implementation folder name -> serialization benchmark directory
IMPLEMENTATIONS: dict[str, Path] = {
    "serde-json": ROOT / "benchmarks/serialization/json/rust/serde-json",
    "simd-json": ROOT / "benchmarks/serialization/json/rust/simd-json",
    "bitcode": ROOT / "benchmarks/serialization/bitcode/rust/bitcode",
    "rkyv": ROOT / "benchmarks/serialization/rkyv/rust/rkyv",
    "flexbuffers": ROOT / "benchmarks/serialization/flexbuffers/rust/flexbuffers",
    "rmp-serde": ROOT / "benchmarks/serialization/messagepack/rust/rmp-serde",
    "msgpacker": ROOT / "benchmarks/serialization/messagepack/rust/msgpacker",
    "prost": ROOT / "benchmarks/serialization/protobuf/rust/prost",
    "capnp": ROOT / "benchmarks/serialization/capnp/rust/capnp",
    "flatbuffers": ROOT / "benchmarks/serialization/flatbuffers/rust/flatbuffers",
    "serde-yaml": ROOT / "benchmarks/serialization/yaml/rust/serde-yaml",
    "toml": ROOT / "benchmarks/serialization/toml/rust/toml",
    "quick-xml": ROOT / "benchmarks/serialization/xml/rust/quick-xml",
    "ini": ROOT / "benchmarks/serialization/ini/rust/ini",
    "kdl": ROOT / "benchmarks/serialization/kdl/rust/kdl",
    "bson": ROOT / "benchmarks/serialization/bson/rust/bson",
    "cbor": ROOT / "benchmarks/serialization/cbor/rust/ciborium",
    "csv": ROOT / "benchmarks/serialization/csv/rust/csv",
    "tsv": ROOT / "benchmarks/serialization/tsv/rust/tsv",
    "json5": ROOT / "benchmarks/serialization/json5/rust/json5",
    "hjson": ROOT / "benchmarks/serialization/hjson/rust/hjson",
    "cjson": ROOT / "benchmarks/serialization/cjson/rust/cjson",
    "plist": ROOT / "benchmarks/serialization/plist/rust/plist",
    "ucl": ROOT / "benchmarks/serialization/ucl/rust/ucl",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_sizes(config_path: Path) -> list[str]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return list(config["parameters"]["sizes"])


def fixture_output_path(format_name: str, spec: str) -> Path:
    domain, tier = spec.split("/", 1)
    return ROOT / "datasets" / "fixtures" / format_name / domain / tier / "fixture.bin"


def record_metadata(spec: str, datasets_index: dict) -> dict:
    entry = datasets_index["datasets"][spec]
    domain = spec.split("/", 1)[0]
    if domain == "logs":
        count = entry["entry_count"]
        field = "entry_count"
    elif domain == "profile":
        count = entry["profile_count"]
        field = "profile_count"
    elif domain == "catalog":
        count = entry["product_count"]
        field = "product_count"
    elif domain == "mesh":
        count = entry["vertex_count"]
        field = "vertex_count"
    else:
        raise ValueError(f"unknown domain in spec: {spec}")

    return {
        field: count,
        "source_canonical_sha256": entry["canonical_sha256"],
        "source_canonical_bytes": entry["canonical_bytes"],
    }


def ensure_built(impl_dir: Path) -> Path:
    bench = impl_dir / "bench"
    if bench.exists():
        return bench

    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(impl_dir / "target")
    tools_bin = str(ROOT / "tools" / "bin")
    env["PATH"] = f"{tools_bin}:{env.get('PATH', '')}"

    install = impl_dir / "install.sh"
    if install.exists():
        subprocess.run(["bash", str(install)], cwd=impl_dir, check=True, env=env)

    metadata = json.loads((impl_dir / "metadata.json").read_text(encoding="utf-8"))
    build_cmd = metadata["hooks"]["build"]
    subprocess.run(build_cmd, cwd=impl_dir, shell=True, check=True, env=env)
    if not bench.exists():
        raise FileNotFoundError(f"bench binary not found after build in {impl_dir}")
    return bench


def emit_fixture(bench: Path, output: Path, spec: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(bench), "--emit-fixture", str(output), spec],
        cwd=bench.parent,
        check=True,
    )


def build_fixtures_index(
    generated: dict[str, dict],
    datasets_index: dict,
) -> dict:
    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "root": "datasets/fixtures",
            "path_pattern": "datasets/fixtures/{format}/{domain}/{tier}",
            "input_file": "fixture.bin",
            "benchmark_parameter": "{domain}/{tier}",
            "source_root": "datasets/shared",
            "source_file": "canonical.json",
        },
        "formats": {
            name: {
                "implementation": name,
                "serialization_bench": str(path.relative_to(ROOT)),
            }
            for name, path in IMPLEMENTATIONS.items()
        },
        "fixtures": generated,
        "source_datasets": datasets_index.get("datasets", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        nargs="*",
        default=None,
        help="Dataset specs to generate (default: all sizes from serialization config).",
    )
    parser.add_argument(
        "--formats",
        nargs="*",
        choices=sorted(IMPLEMENTATIONS),
        default=None,
        help="Limit to specific formats (default: all).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Assume ./bench already exists in each implementation directory.",
    )
    args = parser.parse_args()

    if not DATASETS_INDEX.exists():
        print("datasets/index.json not found; run tools/generate-datasets.py first", file=sys.stderr)
        sys.exit(1)

    datasets_index = json.loads(DATASETS_INDEX.read_text(encoding="utf-8"))
    sizes = args.sizes or load_sizes(SERIALIZATION_CONFIG)
    formats = args.formats or sorted(IMPLEMENTATIONS)

    generated: dict[str, dict] = {}
    if FIXTURES_INDEX.exists():
        existing = json.loads(FIXTURES_INDEX.read_text(encoding="utf-8"))
        generated.update(existing.get("fixtures", {}))

    failures: list[str] = []

    for format_name in formats:
        impl_dir = IMPLEMENTATIONS[format_name]
        print(f"\n==> {format_name}")
        try:
            bench = impl_dir / "bench" if args.skip_build else ensure_built(impl_dir)
        except subprocess.CalledProcessError as error:
            failures.append(f"{format_name}: build failed ({error})")
            print(f"   ERROR: build failed for {format_name}", file=sys.stderr)
            continue
        except FileNotFoundError as error:
            failures.append(f"{format_name}: {error}")
            print(f"   ERROR: {error}", file=sys.stderr)
            continue

        for spec in sizes:
            if spec not in datasets_index["datasets"]:
                print(f"   skip {spec}: missing canonical dataset", file=sys.stderr)
                continue

            output = fixture_output_path(format_name, spec)
            print(f"   {spec} -> {output.relative_to(ROOT)}")
            emit_fixture(bench, output, spec)

            meta = record_metadata(spec, datasets_index)
            key = f"{format_name}/{spec}"
            generated[key] = {
                "format": format_name,
                "parameter_size": spec,
                "fixture_path": str(output.relative_to(ROOT)),
                "fixture_bytes": output.stat().st_size,
                "fixture_sha256": sha256_file(output),
                **meta,
            }

    FIXTURES_INDEX.parent.mkdir(parents=True, exist_ok=True)
    index = build_fixtures_index(generated, datasets_index)
    FIXTURES_INDEX.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    datasets_index.setdefault("fixtures_layout", index["layout"])
    datasets_index["fixtures_count"] = len(generated)
    DATASETS_INDEX.write_text(json.dumps(datasets_index, indent=2) + "\n", encoding="utf-8")

    print(f"\nwrote {FIXTURES_INDEX} ({len(generated)} fixtures)")
    if failures:
        print("\nFailures:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
