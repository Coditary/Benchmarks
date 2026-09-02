#!/usr/bin/env python3
"""Scaffold text-format parsing benchmarks (YAML, TOML, XML, INI, KDL) for Rust and C++."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH_SUPPORT_SERIAL = "../../../rust/bench-support"
BENCH_SUPPORT_DESER = "../../../../serialization/rust/bench-support"
BENCH_SUPPORT_CPP = "../../../../../tools/cpp/bench-support/include"
INSTALL_RUST_SERIAL = "../../../rust/install-rust.sh"
INSTALL_RUST_DESER = "../../../../rust/install-rust.sh"
INSTALL_CPP = "../../../../../tools/cpp/install-cpp.sh"
CONFIG_TEMPLATE = ROOT / "benchmarks/serialization/json/config.json"

BUILD_SH = """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
rm -rf "$BUILD_DIR"
cmake -S "$SCRIPT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build "$BUILD_DIR" -j"$(nproc)"
cp "$BUILD_DIR/bench" "$SCRIPT_DIR/bench"
"""

FORMATS = [
    {
        "format_dir": "yaml",
        "fixture_key": "serde-yaml",
        "rust_impl": "serde-yaml",
        "rust_crate": "yaml-serialize-serde-yaml",
        "deser_crate": "yaml-deserialize-serde-yaml",
        "feature": "yaml",
        "serialize_fn": "yaml",
        "deserialize_fn": "yaml",
        "cpp_impl": "yaml-cpp",
        "cpp_dep": "bench_link_yaml_cpp",
        "cpp_namespace": "yaml_bench",
        "cpp_header": "bench/text/yaml.hpp",
        "tags": ["yaml", "text", "config"],
    },
    {
        "format_dir": "toml",
        "fixture_key": "toml",
        "rust_impl": "toml",
        "rust_crate": "toml-serialize",
        "deser_crate": "toml-deserialize",
        "feature": "toml",
        "serialize_fn": "toml_format",
        "deserialize_fn": "toml_format",
        "cpp_impl": "tomlplusplus",
        "cpp_dep": "bench_link_tomlplusplus",
        "cpp_namespace": "toml_bench",
        "cpp_header": "bench/text/toml.hpp",
        "tags": ["toml", "text", "config"],
    },
    {
        "format_dir": "xml",
        "fixture_key": "quick-xml",
        "rust_impl": "quick-xml",
        "rust_crate": "xml-serialize-quick-xml",
        "deser_crate": "xml-deserialize-quick-xml",
        "feature": "xml",
        "serialize_fn": "xml",
        "deserialize_fn": "xml",
        "cpp_impl": "pugixml",
        "cpp_dep": "bench_link_pugixml",
        "cpp_namespace": "xml_bench",
        "cpp_header": "bench/text/xml.hpp",
        "tags": ["xml", "text", "markup"],
    },
    {
        "format_dir": "ini",
        "fixture_key": "ini",
        "rust_impl": "ini",
        "rust_crate": "ini-serialize",
        "deser_crate": "ini-deserialize",
        "feature": "ini",
        "serialize_fn": "ini",
        "deserialize_fn": "ini",
        "cpp_impl": "inih",
        "cpp_dep": None,
        "cpp_namespace": "ini_bench",
        "cpp_header": "bench/text/ini.hpp",
        "tags": ["ini", "text", "config"],
    },
    {
        "format_dir": "kdl",
        "fixture_key": "kdl",
        "rust_impl": "kdl",
        "rust_crate": "kdl-serialize",
        "deser_crate": "kdl-deserialize",
        "feature": "kdl",
        "serialize_fn": "kdl",
        "deserialize_fn": "kdl",
        "cpp_impl": "kdl-cpp",
        "cpp_dep": None,
        "cpp_namespace": "kdl_bench",
        "cpp_header": "bench/text/kdl.hpp",
        "tags": ["kdl", "text", "config"],
    },
]


def write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def config_for(domain: str, format_dir: str) -> dict:
    base = json.loads(CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    base["domain"] = domain
    base["task_name"] = format_dir
    if domain == "deserialization":
        base["description"] = (
            f"{format_dir.upper()} parsing of shared wire fixtures (internal timing, load excluded)."
        )
    else:
        base["description"] = (
            f"{format_dir.upper()} encoding of shared datasets (internal timing, load excluded)."
        )
    return base


def rust_serialize_main(item: dict) -> str:
    fn = item["serialize_fn"]
    return f"""use std::env;
use std::time::Instant;

use bench_support::dataset::load;
use bench_support::emit::try_emit_fixture;
use bench_support::serialize::{fn};
use bench_support::timing::{{print_result, run_with_setup}};

fn main() {{
    if try_emit_fixture(|data| {fn}(&data)) {{
        return;
    }}

    let dataset = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let data = load(&dataset);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_with_setup(load_seconds, data, {fn});
    print_result(&result);
}}
"""


def rust_deserialize_main(item: dict) -> str:
    fn = item["deserialize_fn"]
    return f"""use std::env;
use std::time::Instant;

use bench_support::deserialize::{fn};
use bench_support::fixtures::load_fixture_bytes;
use bench_support::timing::{{print_result, run_deserialize_with_setup}};

const FORMAT: &str = "{item['fixture_key']}";

fn main() {{
    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let payload = load_fixture_bytes(FORMAT, &spec);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_deserialize_with_setup(load_seconds, payload, |bytes| {{
        {fn}(&spec, bytes)
    }});
    print_result(&result);
}}
"""


def rust_serialize_cargo(item: dict) -> str:
    fn = item["serialize_fn"].split("::")[-1]
    extra = ""
    if item["feature"] == "yaml":
        extra = 'serde_yaml = "0.9"\n'
    elif item["feature"] == "toml":
        extra = 'toml = "0.8"\n'
    return f"""[package]
name = "{item['rust_crate']}"
version = "0.1.0"
edition = "2021"
publish = false

[dependencies]
bench-support = {{ path = "{BENCH_SUPPORT_SERIAL}", features = ["{item['feature']}"] }}
{extra}
[profile.release]
lto = true
codegen-units = 1
"""


def rust_deserialize_cargo(item: dict) -> str:
    return f"""[package]
name = "{item['deser_crate']}"
version = "0.1.0"
edition = "2021"
publish = false

[dependencies]
bench-support = {{ path = "{BENCH_SUPPORT_DESER}", features = ["{item['feature']}"] }}

[profile.release]
lto = true
codegen-units = 1
"""


def cpp_serialize_main(item: dict) -> str:
    return f"""#include <iostream>
#include <string>
#include <vector>

#include "{item['cpp_header']}"
#include "bench/dataset.hpp"
#include "bench/timing.hpp"

int main(int argc, char** argv) {{
    if (argc < 2) {{
        std::cerr << "usage: bench <domain>/<tier>\\n";
        return 1;
    }}
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_with_setup(load_seconds, data, {item['cpp_namespace']}::encode);
    benchkit::print_result(result);
    return 0;
}}
"""


def cpp_deserialize_main(item: dict) -> str:
    return f"""#include <iostream>
#include <string>
#include <vector>

#include "{item['cpp_header']}"
#include "bench/dataset.hpp"
#include "bench/paths.hpp"
#include "bench/timing.hpp"

int main(int argc, char** argv) {{
    if (argc < 2) {{
        std::cerr << "usage: bench <domain>/<tier>\\n";
        return 1;
    }}
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_fixture_bytes("{item['fixture_key']}", spec);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload,
        [spec](const std::vector<std::uint8_t>& bytes) -> benchkit::Dataset {{
            return {item['cpp_namespace']}::decode(spec, bytes);
        }});
    benchkit::print_result(result);
    return 0;
}}
"""


def cpp_cmake_serialize(item: dict) -> str:
    dep_line = f"{item['cpp_dep']}(bench)\n" if item.get("cpp_dep") else ""
    return f"""cmake_minimum_required(VERSION 3.16)
project({item['format_dir']}_serialize_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("../../../../../tools/cpp/cmake/BenchDeps.cmake")
bench_fetch_nlohmann_json()
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT_CPP}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
{dep_line}bench_link_z(bench)
"""


def cpp_cmake_deserialize(item: dict) -> str:
    dep_line = f"{item['cpp_dep']}(bench)\n" if item.get("cpp_dep") else ""
    return f"""cmake_minimum_required(VERSION 3.16)
project({item['format_dir']}_deserialize_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("../../../../../tools/cpp/cmake/BenchDeps.cmake")
bench_fetch_nlohmann_json()
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT_CPP}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
{dep_line}bench_link_z(bench)
"""


def scaffold_rust_serialize(item: dict) -> None:
    dest = ROOT / "benchmarks/serialization" / item["format_dir"] / "rust" / item["rust_impl"]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "src").mkdir(exist_ok=True)
    (dest / "src/main.rs").write_text(rust_serialize_main(item))
    (dest / "Cargo.toml").write_text(rust_serialize_cargo(item))
    write_executable(dest / "install.sh", f'#!/usr/bin/env bash\nset -euo pipefail\nexec "$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)/{INSTALL_RUST_SERIAL}"\n')
    metadata = {
        "language": "Rust",
        "implementation": item["rust_impl"],
        "timing": "internal",
        "run_cmd": "./bench {size}",
        "tags": ["rust", "serialize"] + item["tags"],
        "hooks": {
            "install": "./install.sh",
            "build": f"cargo build --release && cp target/release/{item['rust_crate']} ./bench",
            "clean": "cargo clean && rm -f bench",
        },
        "source_files": ["src/main.rs", "Cargo.toml"],
        "artifact_path": "bench",
        "dataset": {
            "root": "datasets/shared",
            "parameter": "{domain}/{tier}",
            "input": "canonical.json",
        },
        "notes": f"{item['format_dir'].upper()} encode from canonical dataset (untimed load, timed serialize).",
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    config_path = ROOT / "benchmarks/serialization" / item["format_dir"] / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config_for("serialization", item["format_dir"]), indent=2) + "\n")


def scaffold_rust_deserialize(item: dict) -> None:
    dest = ROOT / "benchmarks/deserialization" / item["format_dir"] / "rust" / item["rust_impl"]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "src").mkdir(exist_ok=True)
    (dest / "src/main.rs").write_text(rust_deserialize_main(item))
    (dest / "Cargo.toml").write_text(rust_deserialize_cargo(item))
    write_executable(dest / "install.sh", f'#!/usr/bin/env bash\nset -euo pipefail\nexec "$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)/{INSTALL_RUST_DESER}"\n')
    metadata = {
        "language": "Rust",
        "implementation": item["rust_impl"],
        "timing": "internal",
        "run_cmd": "./bench {size}",
        "tags": ["rust", "deserialize"] + item["tags"],
        "hooks": {
            "install": "./install.sh",
            "build": f"cargo build --release && cp target/release/{item['deser_crate']} ./bench",
            "clean": "cargo clean && rm -f bench",
        },
        "source_files": ["src/main.rs", "Cargo.toml"],
        "artifact_path": "bench",
        "dataset": {
            "root": "datasets/fixtures",
            "parameter": "{domain}/{tier}",
            "input": "fixture.bin",
        },
        "notes": "Loads pre-generated wire fixture once (untimed), then measures parse + materialization.",
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    config_path = ROOT / "benchmarks/deserialization" / item["format_dir"] / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config_for("deserialization", item["format_dir"]), indent=2) + "\n")


def scaffold_cpp(item: dict, domain: str) -> None:
    is_deser = domain == "deserialization"
    dest = ROOT / "benchmarks" / domain / item["format_dir"] / "cpp" / item["cpp_impl"]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "main.cpp").write_text(cpp_deserialize_main(item) if is_deser else cpp_serialize_main(item))
    (dest / "CMakeLists.txt").write_text(
        cpp_cmake_deserialize(item) if is_deser else cpp_cmake_serialize(item)
    )
    write_executable(dest / "build.sh", BUILD_SH)
    write_executable(dest / "install.sh", f'#!/usr/bin/env bash\nset -euo pipefail\nexec "$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)/{INSTALL_CPP}"\n')
    metadata = {
        "language": "C++",
        "implementation": item["cpp_impl"],
        "timing": "internal",
        "run_cmd": "./bench {size}",
        "tags": ["cpp"] + (["deserialize"] if is_deser else ["serialize"]) + item["tags"],
        "hooks": {
            "install": "./install.sh",
            "build": "./build.sh",
            "clean": "rm -rf build bench",
        },
        "source_files": ["main.cpp", "CMakeLists.txt"],
        "artifact_path": "bench",
        "dataset": {
            "root": "datasets/shared" if not is_deser else "datasets/fixtures",
            "parameter": "{domain}/{tier}",
            "input": "canonical.json" if not is_deser else "fixture.bin",
        },
        "notes": (
            f"C++ {item['format_dir'].upper()} parse from wire fixture."
            if is_deser
            else f"C++ {item['format_dir'].upper()} encode from canonical dataset."
        ),
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


def update_generate_fixtures() -> None:
    path = ROOT / "tools/generate-fixtures.py"
    text = path.read_text(encoding="utf-8")
    marker = '    "flatbuffers": ROOT / "benchmarks/serialization/flatbuffers/rust/flatbuffers",\n}'
    additions = ""
    for item in FORMATS:
        key = item["fixture_key"]
        rel = f'ROOT / "benchmarks/serialization/{item["format_dir"]}/rust/{item["rust_impl"]}"'
        line = f'    "{key}": {rel},\n'
        if f'"{key}"' not in text:
            additions += line
    if additions:
        text = text.replace(marker, f'    "flatbuffers": ROOT / "benchmarks/serialization/flatbuffers/rust/flatbuffers",\n{additions}}}')
        path.write_text(text, encoding="utf-8")


def main() -> None:
    for item in FORMATS:
        scaffold_rust_serialize(item)
        scaffold_rust_deserialize(item)
        scaffold_cpp(item, "serialization")
        scaffold_cpp(item, "deserialization")
        print(f"scaffolded {item['format_dir']}")
    update_generate_fixtures()
    print("updated tools/generate-fixtures.py")


if __name__ == "__main__":
    main()
