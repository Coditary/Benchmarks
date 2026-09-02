#!/usr/bin/env python3
"""Scaffold extra format benchmarks (BSON, CBOR, CSV, TSV, JSON5, HJSON, CJSON, plist, UCL)."""

from __future__ import annotations

import importlib.util
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "scaffold_text_format_benchmarks",
    ROOT / "tools/scaffold-text-format-benchmarks.py",
)
_stfb = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_stfb)

config_for = _stfb.config_for
cpp_cmake_deserialize = _stfb.cpp_cmake_deserialize
cpp_cmake_serialize = _stfb.cpp_cmake_serialize
cpp_deserialize_main = _stfb.cpp_deserialize_main
cpp_serialize_main = _stfb.cpp_serialize_main
rust_deserialize_cargo = _stfb.rust_deserialize_cargo
rust_deserialize_main = _stfb.rust_deserialize_main
rust_serialize_cargo = _stfb.rust_serialize_cargo
rust_serialize_main = _stfb.rust_serialize_main
scaffold_cpp = _stfb.scaffold_cpp
scaffold_rust_deserialize = _stfb.scaffold_rust_deserialize
scaffold_rust_serialize = _stfb.scaffold_rust_serialize
write_executable = _stfb.write_executable

FORMATS = [
    {
        "format_dir": "bson",
        "fixture_key": "bson",
        "rust_impl": "bson",
        "rust_crate": "bson-serialize",
        "deser_crate": "bson-deserialize",
        "feature": "bson",
        "serialize_fn": "bson",
        "deserialize_fn": "bson",
        "cpp_impl": "nlohmann-bson",
        "cpp_dep": "bench_link_nlohmann_json",
        "cpp_namespace": "bson_bench",
        "cpp_header": "bench/text/bson.hpp",
        "tags": ["bson", "binary", "document"],
    },
    {
        "format_dir": "cbor",
        "fixture_key": "cbor",
        "rust_impl": "ciborium",
        "rust_crate": "cbor-serialize-ciborium",
        "deser_crate": "cbor-deserialize-ciborium",
        "feature": "cbor",
        "serialize_fn": "cbor",
        "deserialize_fn": "cbor",
        "cpp_impl": "nlohmann-cbor",
        "cpp_dep": "bench_link_nlohmann_json",
        "cpp_namespace": "cbor_bench",
        "cpp_header": "bench/text/cbor.hpp",
        "tags": ["cbor", "binary", "document"],
    },
    {
        "format_dir": "csv",
        "fixture_key": "csv",
        "rust_impl": "csv",
        "rust_crate": "csv-serialize",
        "deser_crate": "csv-deserialize",
        "feature": "csv",
        "serialize_fn": "csv",
        "deserialize_fn": "csv",
        "cpp_impl": "csv-cpp",
        "cpp_dep": None,
        "cpp_namespace": "csv_bench",
        "cpp_header": "bench/text/csv.hpp",
        "tags": ["csv", "text", "tabular"],
    },
    {
        "format_dir": "tsv",
        "fixture_key": "tsv",
        "rust_impl": "tsv",
        "rust_crate": "tsv-serialize",
        "deser_crate": "tsv-deserialize",
        "feature": "tsv",
        "serialize_fn": "tsv",
        "deserialize_fn": "tsv",
        "cpp_impl": "tsv-cpp",
        "cpp_dep": None,
        "cpp_namespace": "tsv_bench",
        "cpp_header": "bench/text/tsv.hpp",
        "tags": ["tsv", "text", "tabular"],
    },
    {
        "format_dir": "json5",
        "fixture_key": "json5",
        "rust_impl": "json5",
        "rust_crate": "json5-serialize",
        "deser_crate": "json5-deserialize",
        "feature": "json5",
        "serialize_fn": "json5_format",
        "deserialize_fn": "json5_format",
        "cpp_impl": "json5-cpp",
        "cpp_dep": None,
        "cpp_namespace": "json5_bench",
        "cpp_header": "bench/text/json5.hpp",
        "tags": ["json5", "text", "config"],
    },
    {
        "format_dir": "hjson",
        "fixture_key": "hjson",
        "rust_impl": "hjson",
        "rust_crate": "hjson-serialize",
        "deser_crate": "hjson-deserialize",
        "feature": "hjson",
        "serialize_fn": "hjson_format",
        "deserialize_fn": "hjson_format",
        "cpp_impl": "hjson-cpp",
        "cpp_dep": "bench_link_hjson_cpp",
        "cpp_namespace": "hjson_bench",
        "cpp_header": "bench/text/hjson.hpp",
        "tags": ["hjson", "text", "config"],
    },
    {
        "format_dir": "cjson",
        "fixture_key": "cjson",
        "rust_impl": "cjson",
        "rust_crate": "cjson-serialize",
        "deser_crate": "cjson-deserialize",
        "feature": "cjson",
        "serialize_fn": "cjson",
        "deserialize_fn": "cjson",
        "cpp_impl": "cjson",
        "cpp_dep": "bench_link_cjson",
        "cpp_namespace": "cjson_bench",
        "cpp_header": "bench/text/cjson.hpp",
        "tags": ["cjson", "text", "json"],
    },
    {
        "format_dir": "plist",
        "fixture_key": "plist",
        "rust_impl": "plist",
        "rust_crate": "plist-serialize",
        "deser_crate": "plist-deserialize",
        "feature": "plist",
        "serialize_fn": "plist_format",
        "deserialize_fn": "plist_format",
        "cpp_impl": "libplist",
        "cpp_dep": "bench_link_pugixml",
        "cpp_namespace": "plist_bench",
        "cpp_header": "bench/text/plist.hpp",
        "tags": ["plist", "text", "apple"],
    },
    {
        "format_dir": "ucl",
        "fixture_key": "ucl",
        "rust_impl": "ucl",
        "rust_crate": "ucl-serialize",
        "deser_crate": "ucl-deserialize",
        "feature": "ucl",
        "serialize_fn": "ucl",
        "deserialize_fn": "ucl",
        "cpp_impl": "libucl",
        "cpp_dep": None,
        "cpp_namespace": "ucl_bench",
        "cpp_header": "bench/text/ucl.hpp",
        "tags": ["ucl", "text", "config"],
    },
]


def update_generate_fixtures() -> None:
    path = ROOT / "tools/generate-fixtures.py"
    text = path.read_text(encoding="utf-8")
    marker = '    "kdl": ROOT / "benchmarks/serialization/kdl/rust/kdl",\n}'
    additions = ""
    for item in FORMATS:
        key = item["fixture_key"]
        rel = f'ROOT / "benchmarks/serialization/{item["format_dir"]}/rust/{item["rust_impl"]}"'
        line = f'    "{key}": {rel},\n'
        if f'"{key}"' not in text:
            additions += line
    if additions:
        text = text.replace(
            marker,
            f'    "kdl": ROOT / "benchmarks/serialization/kdl/rust/kdl",\n{additions}}}',
        )
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
