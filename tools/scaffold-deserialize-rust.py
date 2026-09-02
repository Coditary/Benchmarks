#!/usr/bin/env python3
"""Scaffold Rust deserialization benchmark crates."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESER = ROOT / "benchmarks" / "deserialization"
SERIAL = ROOT / "benchmarks" / "serialization"
BENCH_SUPPORT = "../../../../serialization/rust/bench-support"
INSTALL = '../../../rust/install-rust.sh'

IMPLS = [
    {
        "format_dir": "json",
        "impl": "serde-json",
        "crate": "json-deserialize-serde-json",
        "format": "serde-json",
        "decode_fn": "bench_support::deserialize::json",
        "features": "",
        "extra_deps": "",
        "extra_mods": "",
        "copy_from": None,
    },
    {
        "format_dir": "json",
        "impl": "simd-json",
        "crate": "json-deserialize-simd-json",
        "format": "simd-json",
        "decode_fn": "bench_support::deserialize::simd_json",
        "features": ', features = ["simd-json"]',
        "extra_deps": "",
        "extra_mods": "",
        "copy_from": None,
    },
    {
        "format_dir": "bitcode",
        "impl": "bitcode",
        "crate": "bitcode-deserialize",
        "format": "bitcode",
        "decode_fn": "bench_support::deserialize::bitcode",
        "features": ', features = ["bitcode"]',
        "extra_deps": 'bitcode = "0.6"\n',
        "extra_mods": "",
        "copy_from": None,
    },
    {
        "format_dir": "rkyv",
        "impl": "rkyv",
        "crate": "rkyv-deserialize",
        "format": "rkyv",
        "decode_fn": "bench_support::deserialize::rkyv",
        "features": ', features = ["rkyv"]',
        "extra_deps": 'rkyv = "0.8"\n',
        "extra_mods": "",
        "copy_from": None,
    },
    {
        "format_dir": "flexbuffers",
        "impl": "flexbuffers",
        "crate": "flexbuffers-deserialize",
        "format": "flexbuffers",
        "decode_fn": "bench_support::deserialize::flexbuffers",
        "features": ', features = ["flexbuffers"]',
        "extra_deps": 'flexbuffers = "25"\n',
        "extra_mods": "",
        "copy_from": None,
    },
    {
        "format_dir": "messagepack",
        "impl": "rmp-serde",
        "crate": "messagepack-deserialize-rmp-serde",
        "format": "rmp-serde",
        "decode_fn": "bench_support::deserialize::rmp_serde",
        "features": ', features = ["rmp-serde"]',
        "extra_deps": 'rmp-serde = "1"\n',
        "extra_mods": "",
        "copy_from": None,
    },
    {
        "format_dir": "messagepack",
        "impl": "msgpacker",
        "crate": "messagepack-deserialize-msgpacker",
        "format": "msgpacker",
        "decode_fn": "convert::decode",
        "features": "",
        "extra_deps": 'msgpacker = { version = "0.7", features = ["std", "derive"] }\n',
        "extra_mods": "mod convert;\n\n",
        "copy_from": ("messagepack/rust/msgpacker", ["src/convert.rs"]),
        "convert_decode": True,
    },
    {
        "format_dir": "protobuf",
        "impl": "prost",
        "crate": "protobuf-deserialize-prost",
        "format": "prost",
        "decode_fn": "convert::decode",
        "features": "",
        "extra_deps": 'prost = "0.13"\n',
        "extra_mods": "mod convert;\n\n",
        "copy_from": ("protobuf/rust/prost", ["build.rs", "src/convert.rs"]),
        "convert_decode": True,
        "build": True,
    },
    {
        "format_dir": "capnp",
        "impl": "capnp",
        "crate": "capnp-deserialize",
        "format": "capnp",
        "decode_fn": "deserialize::decode",
        "features": "",
        "extra_deps": 'capnp = "0.20"\n',
        "extra_mods": "mod deserialize;\n\n",
        "copy_from": ("capnp/rust/capnp", ["build.rs", "generated"]),
        "capnp": True,
        "build": True,
    },
    {
        "format_dir": "flatbuffers",
        "impl": "flatbuffers",
        "crate": "flatbuffers-deserialize",
        "format": "flatbuffers",
        "decode_fn": "deserialize::decode",
        "features": "",
        "extra_deps": 'flatbuffers = "25"\n',
        "extra_mods": "mod deserialize;\n\n",
        "copy_from": ("flatbuffers/rust/flatbuffers", ["build.rs", "generated"]),
        "flatbuffers": True,
        "build": True,
    },
]

MAIN_TEMPLATE = """use std::env;
use std::time::Instant;

use bench_support::fixtures::load_fixture_bytes;
use bench_support::timing::{{print_result, run_deserialize_with_setup}};

{extra_mods}const FORMAT: &str = "{format}";

fn main() {{
    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let payload = load_fixture_bytes(FORMAT, &spec);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_deserialize_with_setup(load_seconds, payload, |bytes| {{
        {decode_fn}(&spec, bytes)
    }});
    print_result(&result);
}}
"""

CARGO_TEMPLATE = """[package]
name = "{crate}"
version = "0.1.0"
edition = "2021"
publish = false
{build_line}
[dependencies]
bench-support = {{ path = "{bench_support}"{features} }}
{extra_deps}
[profile.release]
lto = true
codegen-units = 1
"""

METADATA_TEMPLATE = {
    "language": "Rust",
    "timing": "internal",
    "run_cmd": "./bench {size}",
    "tags": ["rust", "deserialize"],
    "hooks": {
        "install": "./install.sh",
        "build": "cargo build --release && cp target/release/{crate} ./bench",
        "clean": "cargo clean && rm -f bench",
    },
    "source_files": ["src/main.rs", "Cargo.toml"],
    "artifact_path": "bench",
    "dataset": {
        "root": "datasets/fixtures",
        "parameter": "{domain}/{tier}",
        "input": "fixture.bin",
    },
    "notes": "Loads pre-generated wire fixture once (untimed), then measures decode only.",
}


def write_convert_decode(path: Path) -> None:
    convert_path = path / "src" / "convert.rs"
    text = convert_path.read_text()
    if "pub fn decode" in text:
        return
    decode_fn = '''

pub fn decode(spec: &str, bytes: &[u8]) -> u64 {
    use bench_support::shared::domain_from_spec;
    use msgpacker::Unpackable;
    use prost::Message;

    match domain_from_spec(spec) {
        "logs" => {
            let value = MpackLogDataset::unpack(bytes).expect("decode");
            std::hint::black_box((value.version, value.entries.len()));
            value.entries.len() as u64
        }
        "profile" => {
            let value = MpackProfileDataset::unpack(bytes).expect("decode");
            std::hint::black_box((value.version, value.profiles.len()));
            value.profiles.len() as u64
        }
        "mesh" => {
            let value = MpackMeshDataset::unpack(bytes).expect("decode");
            std::hint::black_box((value.version, value.vertices.len()));
            value.vertices.len() as u64
        }
        "catalog" => {
            let value = MpackCatalogDataset::unpack(bytes).expect("decode");
            std::hint::black_box((value.version, value.products.len()));
            value.products.len() as u64
        }
        other => panic!("unknown dataset domain: {other}"),
    }
}
'''
    if "MpackLogDataset" in text:
        convert_path.write_text(text + decode_fn.replace("use prost::Message;\n\n", ""))
    else:
        decode_fn_prost = decode_fn.replace("msgpacker::Unpackable", "prost::Message").replace(
            "MpackLogDataset::unpack(bytes)", "bench::LogDataset::decode(bytes)"
        ).replace("MpackProfileDataset::unpack(bytes)", "bench::ProfileDataset::decode(bytes)"
        ).replace("MpackMeshDataset::unpack(bytes)", "bench::MeshDataset::decode(bytes)"
        ).replace("MpackCatalogDataset::unpack(bytes)", "bench::CatalogDataset::decode(bytes)"
        ).replace("use msgpacker::Unpackable;\n    ", "")
        convert_path.write_text(text + decode_fn_prost)


def write_capnp_deserialize(path: Path) -> None:
    (path / "src" / "deserialize.rs").write_text(
        CAPNP_DESERIALIZE
    )
    main = (path / "src" / "main.rs").read_text()
    if "mod benchmark_capnp" not in main:
        (path / "src" / "main.rs").write_text(
            "mod benchmark_capnp {\n"
            '    include!(concat!(env!("OUT_DIR"), "/benchmark_capnp.rs"));\n'
            "}\n\n" + main
        )


def write_flatbuffers_deserialize(path: Path) -> None:
    (path / "src" / "deserialize.rs").write_text(
        FLATBUFFERS_DESERIALIZE
    )


CAPNP_DESERIALIZE = '''use bench_support::shared::domain_from_spec;

use crate::benchmark_capnp::{
    catalog_dataset, log_dataset, mesh_dataset, profile_dataset,
};

pub fn decode(spec: &str, bytes: &[u8]) -> u64 {
    match domain_from_spec(spec) {
        "logs" => decode_logs(bytes),
        "profile" => decode_profile(bytes),
        "mesh" => decode_mesh(bytes),
        "catalog" => decode_catalog(bytes),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn decode_logs(bytes: &[u8]) -> u64 {
    let message = capnp::serialize::read_message(
        &mut &bytes[..],
        capnp::message::ReaderOptions::new(),
    )
    .expect("decode");
    let root = message
        .get_root::<log_dataset::Reader>()
        .expect("root");
    let version = root.get_version();
    let entries = root.get_entries().expect("entries");
    std::hint::black_box((version, entries.len()));
    entries.len() as u64
}

fn decode_profile(bytes: &[u8]) -> u64 {
    let message = capnp::serialize::read_message(
        &mut &bytes[..],
        capnp::message::ReaderOptions::new(),
    )
    .expect("decode");
    let root = message
        .get_root::<profile_dataset::Reader>()
        .expect("root");
    let version = root.get_version();
    let profiles = root.get_profiles().expect("profiles");
    std::hint::black_box((version, profiles.len()));
    profiles.len() as u64
}

fn decode_mesh(bytes: &[u8]) -> u64 {
    let message = capnp::serialize::read_message(
        &mut &bytes[..],
        capnp::message::ReaderOptions::new(),
    )
    .expect("decode");
    let root = message
        .get_root::<mesh_dataset::Reader>()
        .expect("root");
    let version = root.get_version();
    let vertices = root.get_vertices().expect("vertices");
    std::hint::black_box((version, vertices.len()));
    vertices.len() as u64
}

fn decode_catalog(bytes: &[u8]) -> u64 {
    let message = capnp::serialize::read_message(
        &mut &bytes[..],
        capnp::message::ReaderOptions::new(),
    )
    .expect("decode");
    let root = message
        .get_root::<catalog_dataset::Reader>()
        .expect("root");
    let version = root.get_version();
    let products = root.get_products().expect("products");
    std::hint::black_box((version, products.len()));
    products.len() as u64
}
'''

FLATBUFFERS_DESERIALIZE = '''use bench_support::shared::domain_from_spec;

mod benchmark_generated {
    include!(concat!(env!("OUT_DIR"), "/benchmark_generated.rs"));
}

use benchmark_generated::benchmark::{
    CatalogDataset, LogDataset, MeshDataset, ProfileDataset,
};

pub fn decode(spec: &str, bytes: &[u8]) -> u64 {
    match domain_from_spec(spec) {
        "logs" => decode_logs(bytes),
        "profile" => decode_profile(bytes),
        "mesh" => decode_mesh(bytes),
        "catalog" => decode_catalog(bytes),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn decode_logs(bytes: &[u8]) -> u64 {
    let root = flatbuffers::root::<LogDataset>(bytes).expect("decode");
    let version = root.version();
    let entries = root.entries().map(|v| v.len()).unwrap_or(0);
    std::hint::black_box((version, entries));
    entries as u64
}

fn decode_profile(bytes: &[u8]) -> u64 {
    let root = flatbuffers::root::<ProfileDataset>(bytes).expect("decode");
    let version = root.version();
    let profiles = root.profiles().map(|v| v.len()).unwrap_or(0);
    std::hint::black_box((version, profiles));
    profiles as u64
}

fn decode_mesh(bytes: &[u8]) -> u64 {
    let root = flatbuffers::root::<MeshDataset>(bytes).expect("decode");
    let version = root.version();
    let vertices = root.vertices().map(|v| v.len()).unwrap_or(0);
    std::hint::black_box((version, vertices));
    vertices as u64
}

fn decode_catalog(bytes: &[u8]) -> u64 {
    let root = flatbuffers::root::<CatalogDataset>(bytes).expect("decode");
    let version = root.version();
    let products = root.products().map(|v| v.len()).unwrap_or(0);
    std::hint::black_box((version, products));
    products as u64
}
'''


def main() -> None:
    for item in IMPLS:
        dest = DESER / item["format_dir"] / "rust" / item["impl"]
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "src").mkdir(exist_ok=True)

        build_line = 'build = "build.rs"\n' if item.get("build") else ""
        (dest / "Cargo.toml").write_text(
            CARGO_TEMPLATE.format(
                crate=item["crate"],
                build_line=build_line,
                bench_support=BENCH_SUPPORT,
                features=item["features"],
                extra_deps=item["extra_deps"],
            )
        )

        (dest / "src" / "main.rs").write_text(
            MAIN_TEMPLATE.format(
                extra_mods=item["extra_mods"],
                format=item["format"],
                decode_fn=item["decode_fn"],
            )
        )

        (dest / "install.sh").write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            f'"$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)/{INSTALL}"\n'
        )
        (dest / "install.sh").chmod(0o755)

        metadata = json.loads(json.dumps(METADATA_TEMPLATE))
        metadata["implementation"] = item["impl"]
        metadata["hooks"]["build"] = (
            f"cargo build --release && cp target/release/{item['crate']} ./bench"
        )
        metadata["tags"] = metadata["tags"] + [item["format_dir"], item["impl"]]
        (dest / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

        if item.get("copy_from"):
            serial_base = SERIAL / item["copy_from"][0]
            for rel in item["copy_from"][1]:
                src = serial_base / rel
                target = dest / rel
                if src.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(src, target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, target)

        if item.get("convert_decode"):
            write_convert_decode(dest)

        if item.get("capnp"):
            write_capnp_deserialize(dest)

        if item.get("flatbuffers"):
            write_flatbuffers_deserialize(dest)

        print(f"scaffolded {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
