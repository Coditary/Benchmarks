#!/usr/bin/env python3
"""Scaffold Rust compression and decompression benchmark crates."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "benchmarks" / "compression"
DECOMP = ROOT / "benchmarks" / "decompression"
BENCH_SUPPORT = "../../../rust/bench-support"
SERIAL_TIMING = "../../../../serialization/rust/bench-support"
INSTALL = "../../../rust/install-rust.sh"

SIZES = [
    "logs/10",
    "logs/100",
    "logs/1000",
    "logs/10k",
    "logs/100k",
    "profile/10",
    "profile/100",
    "profile/1000",
    "profile/10k",
    "profile/100k",
    "catalog/10",
    "catalog/100",
    "catalog/1000",
    "catalog/10k",
    "catalog/100k",
    "mesh/100",
    "mesh/1000",
    "mesh/10k",
    "mesh/100k",
    "random/64k",
    "random/256k",
    "random/1m",
    "random/4m",
    "sparse/64k",
    "sparse/256k",
    "sparse/1m",
    "english/64k",
    "english/256k",
    "english/1m",
    "repetitive/64k",
    "repetitive/256k",
    "repetitive/1m",
]

CI_SIZES = [
    "logs/10",
    "profile/10",
    "catalog/10",
    "mesh/100",
    "random/64k",
    "sparse/64k",
    "english/64k",
    "repetitive/64k",
]

CONFIG = {
    "parameters": {
        "sizes": SIZES,
        "element_type": "fixture",
    },
    "benchmark": {
        "warmup": 3,
        "min_runs": 10,
        "max_runs": 50,
        "runs": None,
    },
    "ci": {
        "sizes": CI_SIZES,
        "benchmark": {
            "warmup": 2,
            "min_runs": 5,
            "max_runs": 20,
        },
    },
}

CODECS = [
    ("zstd", "zstd", "zstd"),
    ("gzip", "gzip", "gzip"),
    ("zlib", "zlib", "zlib"),
    ("deflate", "deflate", "deflate"),
    ("lz4", "lz4", "lz4"),
    ("brotli", "brotli", "brotli"),
    ("snappy", "snappy", "snappy"),
    ("bzip2", "bzip2", "bzip2"),
    ("xz", "xz", "xz"),
    ("lzma", "lzma", "lzma"),
    ("lzf", "lzf", "lzf"),
    ("fastlz", "fastlz", "fastlz"),
    ("minilzo", "minilzo", "minilzo"),
    ("lzfse", "lzfse", "lzfse"),
    ("libdeflate", "libdeflate", "libdeflate"),
    ("zopfli", "zopfli", "zopfli"),
    ("zlib-ng", "zlib-ng", "zlib_ng"),
]

COMPRESS_MAIN = """use std::env;
use std::time::Instant;

use bench_support::timing::{{print_result, run_with_setup}};
use compression_bench_support::compress::{fn_name};
use compression_bench_support::emit::try_emit_fixture;
use compression_bench_support::payload::load_payload;

fn main() {{
    if try_emit_fixture({fn_name}) {{
        return;
    }}

    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let payload = load_payload(&spec);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_with_setup(load_seconds, payload, |data| {fn_name}(data));
    print_result(&result);
}}
"""

DECOMPRESS_MAIN = """use std::env;
use std::time::Instant;

use bench_support::timing::{{print_result, run_deserialize_with_setup}};
use compression_bench_support::decompress::{fn_name};
use compression_bench_support::fixtures::load_fixture_bytes;

const CODEC: &str = "{codec}";

fn main() {{
    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let payload = load_fixture_bytes(CODEC, &spec);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_deserialize_with_setup(load_seconds, payload, |bytes| {{
        {fn_name}(bytes)
    }});
    print_result(&result);
}}
"""


def write_config(base: Path, domain: str, task: str, description: str) -> None:
    base.mkdir(parents=True, exist_ok=True)
    payload = {
        "domain": domain,
        "task_name": task,
        "description": description,
        **CONFIG,
    }
    (base / "config.json").write_text(json.dumps(payload, indent=2) + "\n")


def scaffold_codec(codec: str, folder: str, fn_name: str) -> None:
    comp_dir = COMP / folder / "rust" / codec
    decomp_dir = DECOMP / folder / "rust" / codec
    comp_crate = f"compression-{codec}"
    decomp_crate = f"decompression-{codec}"

    write_config(
        COMP / folder,
        "compression",
        folder,
        f"Compression benchmark using {codec}.",
    )
    write_config(
        DECOMP / folder,
        "decompression",
        folder,
        f"Decompression benchmark for pre-compressed {codec} fixtures.",
    )

    for dest, crate_name, main_src, is_decomp in (
        (comp_dir, comp_crate, COMPRESS_MAIN.format(fn_name=fn_name), False),
        (decomp_dir, decomp_crate, DECOMPRESS_MAIN.format(fn_name=fn_name, codec=codec), True),
    ):
        (dest / "src").mkdir(parents=True, exist_ok=True)
        bench_support_path = (
            "../../../../compression/rust/bench-support"
            if is_decomp
            else BENCH_SUPPORT
        )
        (dest / "Cargo.toml").write_text(
            f"""[package]
name = "{crate_name}"
version = "0.1.0"
edition = "2021"
publish = false

[dependencies]
bench-support = {{ path = "{SERIAL_TIMING}" }}
compression-bench-support = {{ path = "{bench_support_path}", features = ["{codec}"] }}

[profile.release]
lto = true
codegen-units = 1
"""
        )
        (dest / "src" / "main.rs").write_text(main_src)
        (dest / "install.sh").write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            f'"$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)/{INSTALL}"\n'
        )
        (dest / "install.sh").chmod(0o755)

        dataset = (
            {
                "root": "datasets/fixtures/compression",
                "parameter": "{domain}/{tier}",
                "input": "fixture.bin",
            }
            if is_decomp
            else {
                "root": "datasets/compression",
                "parameter": "{domain}/{tier}",
                "input": "payload.bin",
            }
        )
        metadata = {
            "language": "Rust",
            "implementation": codec,
            "timing": "internal",
            "run_cmd": "./bench {size}",
            "tags": ["rust", "compression" if not is_decomp else "decompression", codec],
            "hooks": {
                "install": "./install.sh",
                "build": f"cargo build --release && cp target/release/{crate_name} ./bench",
                "clean": "cargo clean && rm -f bench",
            },
            "source_files": ["src/main.rs", "Cargo.toml"],
            "artifact_path": "bench",
            "dataset": dataset,
            "notes": (
                "Loads payload.bin once (untimed), then measures compression only."
                if not is_decomp
                else "Loads pre-compressed fixture once (untimed), then measures decompression only."
            ),
        }
        (dest / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"scaffolded {dest.relative_to(ROOT)}")


def main() -> None:
    for folder, codec, fn_name in CODECS:
        scaffold_codec(codec, folder, fn_name)


if __name__ == "__main__":
    main()
