#!/usr/bin/env python3
"""Scaffold C++ benchmark implementations."""

from __future__ import annotations

import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH_SUPPORT = "../../../../../tools/cpp/bench-support/include"
INSTALL = "../../../../../tools/cpp/install-cpp.sh"
SCHEMA = "../../../../../datasets/shared/schemas"

BUILD_SH = """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
rm -rf "$BUILD_DIR"
cmake -S "$SCRIPT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j"$(nproc)"
cp "$BUILD_DIR/bench" "$SCRIPT_DIR/bench"
"""

INSTALL_SH = """#!/usr/bin/env bash
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/""" + INSTALL + """"
"""

METADATA_TEMPLATE = """{{
  "language": "C++",
  "implementation": "{impl}",
  "timing": "internal",
  "run_cmd": "./bench {{size}}",
  "tags": {tags},
  "hooks": {{
    "install": "./install.sh",
    "build": "./build.sh",
    "clean": "rm -rf build bench"
  }},
  "source_files": {source_files},
  "artifact_path": "bench",
  "dataset": {dataset},
  "notes": "{notes}"
}}
"""

CMAKE_BASE = """cmake_minimum_required(VERSION 3.16)
project({project} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(bench {sources})
target_include_directories(bench PRIVATE "{bench_support}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
{extra_cmake}
{link_libs}
"""


def write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_impl(path: Path, metadata: dict, cmake: str, main_cpp: str, extra: dict[str, str] | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    write_executable(path / "build.sh", BUILD_SH)
    write_executable(path / "install.sh", INSTALL_SH)
    (path / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (path / "CMakeLists.txt").write_text(cmake)
    (path / "main.cpp").write_text(main_cpp)
    if extra:
        for name, content in extra.items():
            (path / name).write_text(content)


def json_serialize() -> None:
    main_cpp = r'''#include <iostream>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "bench/dataset.hpp"
#include "bench/timing.hpp"

namespace {

std::vector<std::uint8_t> serialize_json(const benchkit::Dataset& data) {
    const nlohmann::json json =
        std::visit([](const auto& value) { return nlohmann::json(value); }, data);
    const std::string dumped = json.dump();
    return std::vector<std::uint8_t>(dumped.begin(), dumped.end());
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_with_setup(load_seconds, data, serialize_json);
    benchkit::print_result(result);
    return 0;
}
'''
    cmake = f'''cmake_minimum_required(VERSION 3.16)
project(json_serialize_nlohmann LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include("{BENCH_SUPPORT.replace("/include", "/../cmake")}/BenchDeps.cmake")
bench_fetch_nlohmann_json()

add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{bench_support}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_z(bench)
'''
    metadata = json.loads(
        METADATA_TEMPLATE.format(
            impl="nlohmann-json",
            tags=json.dumps(["cpp", "json", "nlohmann", "text"]),
            source_files=json.dumps(["main.cpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {
                    "root": "datasets/shared",
                    "parameter": "{domain}/{tier}",
                    "input": "canonical.json",
                }
            ),
            notes="Loads canonical JSON once (untimed), then measures nlohmann::json::dump in-process.",
        )
    )
    write_impl(ROOT / "benchmarks/serialization/json/cpp/nlohmann-json", metadata, cmake, main_cpp)


def json_deserialize() -> None:
    main_cpp = r'''#include <iostream>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "bench/dataset.hpp"
#include "bench/paths.hpp"
#include "bench/timing.hpp"

namespace {

benchkit::Dataset decode_json(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const nlohmann::json json =
        nlohmann::json::parse(payload.begin(), payload.end());
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") {
        return benchkit::parse_logs(json);
    }
    if (domain == "profile") {
        return benchkit::parse_profile(json);
    }
    if (domain == "mesh") {
        return benchkit::parse_mesh(json);
    }
    if (domain == "catalog") {
        return benchkit::parse_catalog(json);
    }
    throw std::runtime_error("unknown domain");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_fixture_bytes("serde-json", spec);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, [&](const std::vector<std::uint8_t>& bytes) {
            return decode_json(spec, bytes);
        });
    benchkit::print_result(result);
    return 0;
}
'''
    cmake = CMAKE_BASE.format(
        project="json_deserialize_nlohmann",
        sources="main.cpp",
        bench_support=BENCH_SUPPORT,
        extra_cmake="find_package(nlohmann_json 3.2.0 REQUIRED)",
        link_libs="target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json z)",
    )
    metadata = json.loads(
        METADATA_TEMPLATE.format(
            impl="nlohmann-json",
            tags=json.dumps(["cpp", "json", "nlohmann", "deserialize"]),
            source_files=json.dumps(["main.cpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {
                    "root": "datasets/fixtures",
                    "parameter": "{domain}/{tier}",
                    "input": "fixture.bin",
                }
            ),
            notes="Loads serde-json wire fixture once (untimed), then measures full JSON materialization.",
        )
    )
    write_impl(ROOT / "benchmarks/deserialization/json/cpp/nlohmann-json", metadata, cmake, main_cpp)


def msgpack_serialize() -> None:
    main_cpp = r'''#include <iostream>
#include <sstream>
#include <vector>

#include <msgpack.hpp>

#include "bench/dataset.hpp"
#include "bench/timing.hpp"

namespace {

std::vector<std::uint8_t> serialize_msgpack(const benchkit::Dataset& data) {
  return std::visit(
      [](const auto& value) {
        std::stringstream buffer;
        msgpack::pack(buffer, value);
        const std::string packed = buffer.str();
        return std::vector<std::uint8_t>(packed.begin(), packed.end());
      },
      data);
}

}  // namespace

MSGPACK_ADD_ENUM(benchkit::Dataset::index);  // not used

namespace msgpack {
MSGPACK_API_VERSION_NAMESPACE(MSGPACK_DEFAULT_API_NS) {
namespace adaptor {

template <>
struct pack<benchkit::LogMetadata> {
  template <typename Stream>
  packer<Stream>& operator()(msgpack::packer<Stream>& o, const benchkit::LogMetadata& v) const {
    o.pack_map(5);
    o.pack("status");
    o.pack(v.status);
    o.pack("duration_ms");
    o.pack(v.duration_ms);
    o.pack("bytes_sent");
    o.pack(v.bytes_sent);
    o.pack("user_agent");
    o.pack(v.user_agent);
    o.pack("remote_addr");
    o.pack(v.remote_addr);
    return o;
  }
};

template <>
struct convert<benchkit::LogMetadata> {
  msgpack::object const& operator()(msgpack::object const& o, benchkit::LogMetadata& v) const {
    std::map<std::string, msgpack::object> mapped;
    o.convert(mapped);
    mapped.at("status").convert(v.status);
    mapped.at("duration_ms").convert(v.duration_ms);
    mapped.at("bytes_sent").convert(v.bytes_sent);
    mapped.at("user_agent").convert(v.user_agent);
    mapped.at("remote_addr").convert(v.remote_addr);
    return o;
  }
};

template <>
struct pack<benchkit::LogEntry> {
  template <typename Stream>
  packer<Stream>& operator()(msgpack::packer<Stream>& o, const benchkit::LogEntry& v) const {
    o.pack_map(5);
    o.pack("timestamp");
    o.pack(v.timestamp);
    o.pack("level");
    o.pack(v.level);
    o.pack("message");
    o.pack(v.message);
    o.pack("request_id");
    o.pack(v.request_id);
    o.pack("metadata");
    o.pack(v.metadata);
    return o;
  }
};

template <>
struct convert<benchkit::LogEntry> {
  msgpack::object const& operator()(msgpack::object const& o, benchkit::LogEntry& v) const {
    std::map<std::string, msgpack::object> mapped;
    o.convert(mapped);
    mapped.at("timestamp").convert(v.timestamp);
    mapped.at("level").convert(v.level);
    mapped.at("message").convert(v.message);
    mapped.at("request_id").convert(v.request_id);
    mapped.at("metadata").convert(v.metadata);
    return o;
  }
};

template <>
struct pack<benchkit::LogDataset> {
  template <typename Stream>
  packer<Stream>& operator()(msgpack::packer<Stream>& o, const benchkit::LogDataset& v) const {
    o.pack_map(4);
    o.pack("version");
    o.pack(v.version);
    o.pack("domain");
    o.pack(v.domain);
    o.pack("tier");
    o.pack(v.tier);
    o.pack("entries");
    o.pack(v.entries);
    return o;
  }
};

template <>
struct convert<benchkit::LogDataset> {
  msgpack::object const& operator()(msgpack::object const& o, benchkit::LogDataset& v) const {
    std::map<std::string, msgpack::object> mapped;
    o.convert(mapped);
    mapped.at("version").convert(v.version);
    mapped.at("domain").convert(v.domain);
    mapped.at("tier").convert(v.tier);
    mapped.at("entries").convert(v.entries);
    return o;
  }
};

}  // namespace adaptor
}  // MSGPACK_API_VERSION_NAMESPACE
}  // namespace msgpack

int main(int argc, char** argv) {
  if (argc < 2) {
    std::cerr << "usage: bench <domain>/<tier>\n";
    return 1;
  }
  const std::string spec = argv[1];
  const double load_start = benchkit::now_seconds();
  const benchkit::Dataset data = benchkit::load(spec);
  const double load_seconds = benchkit::now_seconds() - load_start;
  const auto result = benchkit::run_with_setup(load_seconds, data, serialize_msgpack);
  benchkit::print_result(result);
  return 0;
}
'''
    # Simplified msgpack - use map encoding like serde. For full domains, include convert headers.
    # Actually the msgpack adaptors above only cover logs - need all domains or use a simpler approach:
    # pack nlohmann json as msgpack via intermediate - but that's slower prep.
    # For scaffold, use JSON-compatible msgpack by packing json object from dataset.

    main_cpp = r'''#include <iostream>
#include <sstream>
#include <vector>

#include <msgpack.hpp>
#include <nlohmann/json.hpp>

#include "bench/dataset.hpp"
#include "bench/timing.hpp"

namespace {

std::vector<std::uint8_t> serialize_msgpack(const benchkit::Dataset& data) {
    const nlohmann::json json =
        std::visit([](const auto& value) { return nlohmann::json(value); }, data);
    std::stringstream buffer;
    msgpack::pack(buffer, json);
    const std::string packed = buffer.str();
    return std::vector<std::uint8_t>(packed.begin(), packed.end());
}

benchkit::Dataset decode_msgpack(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const msgpack::object_handle handle =
        msgpack::unpack(reinterpret_cast<const char*>(payload.data()), payload.size());
    nlohmann::json json;
    handle.get().convert(json);
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") return benchkit::parse_logs(json);
    if (domain == "profile") return benchkit::parse_profile(json);
    if (domain == "mesh") return benchkit::parse_mesh(json);
    if (domain == "catalog") return benchkit::parse_catalog(json);
    throw std::runtime_error("unknown domain");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_with_setup(load_seconds, data, serialize_msgpack);
    benchkit::print_result(result);
    return 0;
}
'''
    cmake = CMAKE_BASE.format(
        project="msgpack_serialize",
        sources="main.cpp",
        bench_support=BENCH_SUPPORT,
        extra_cmake="find_package(nlohmann_json 3.2.0 REQUIRED)\nfind_path(MSGPACK_INCLUDE_DIR msgpack.hpp)\nif(NOT MSGPACK_INCLUDE_DIR)\n  message(FATAL_ERROR \"msgpack.hpp not found\")\nendif()\ntarget_include_directories(bench PRIVATE ${MSGPACK_INCLUDE_DIR})",
        link_libs="target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json z)",
    )
    metadata = json.loads(
        METADATA_TEMPLATE.format(
            impl="msgpack-cxx",
            tags=json.dumps(["cpp", "messagepack", "binary"]),
            source_files=json.dumps(["main.cpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {"root": "datasets/shared", "parameter": "{domain}/{tier}", "input": "canonical.json"}
            ),
            notes="Canonical dataset to msgpack map encoding (untimed load, timed pack).",
        )
    )
    write_impl(ROOT / "benchmarks/serialization/messagepack/cpp/msgpack-cxx", metadata, cmake, main_cpp)

    deser_main = main_cpp.replace(
        "serialize_msgpack",
        "DECODE_PLACEHOLDER",
    )
    deser_main = r'''#include <iostream>
#include <sstream>
#include <vector>

#include <msgpack.hpp>
#include <nlohmann/json.hpp>

#include "bench/dataset.hpp"
#include "bench/paths.hpp"
#include "bench/timing.hpp"

namespace {

benchkit::Dataset decode_msgpack(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const msgpack::object_handle handle =
        msgpack::unpack(reinterpret_cast<const char*>(payload.data()), payload.size());
    nlohmann::json json;
    handle.get().convert(json);
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") return benchkit::parse_logs(json);
    if (domain == "profile") return benchkit::parse_profile(json);
    if (domain == "mesh") return benchkit::parse_mesh(json);
    if (domain == "catalog") return benchkit::parse_catalog(json);
    throw std::runtime_error("unknown domain");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_fixture_bytes("rmp-serde", spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, [&](const std::vector<std::uint8_t>& bytes) {
            return decode_msgpack(spec, bytes);
        });
    benchkit::print_result(result);
    return 0;
}
'''
    metadata = json.loads(
        METADATA_TEMPLATE.format(
            impl="msgpack-cxx",
            tags=json.dumps(["cpp", "messagepack", "deserialize"]),
            source_files=json.dumps(["main.cpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {"root": "datasets/fixtures", "parameter": "{domain}/{tier}", "input": "fixture.bin"}
            ),
            notes="Loads rmp-serde fixture once (untimed), then measures msgpack decode + materialization.",
        )
    )
    write_impl(ROOT / "benchmarks/deserialization/messagepack/cpp/msgpack-cxx", metadata, cmake, deser_main)


def compression_codec(codec: str, fn_name: str, includes: str, body: str, decompress_body: str,
                      libs: str, pkg: str) -> None:
    comp_main = f'''#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
{includes}

namespace {{

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {{
{body}
}}

}}  // namespace

int main(int argc, char** argv) {{
    if (argc < 2) {{
        std::cerr << "usage: bench <domain>/<tier>\\n";
        return 1;
    }}
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_compression_payload(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_with_setup(load_seconds, payload, compress_payload);
    benchkit::print_result(result);
    return 0;
}}
'''
    decomp_main = f'''#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
{includes}

namespace {{

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {{
{decompress_body}
}}

}}  // namespace

int main(int argc, char** argv) {{
    if (argc < 2) {{
        std::cerr << "usage: bench <domain>/<tier>\\n";
        return 1;
    }}
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_compression_fixture("{codec}", spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, decompress_payload);
    benchkit::print_result(result);
    return 0;
}}
'''
    cmake = CMAKE_BASE.format(
        project=f"compression_{codec}",
        sources="main.cpp",
        bench_support=BENCH_SUPPORT,
        extra_cmake=pkg,
        link_libs=f"target_link_libraries(bench PRIVATE {libs} z)",
    )
    comp_meta = json.loads(
        METADATA_TEMPLATE.format(
            impl=f"lib{codec}" if codec not in {"zlib", "deflate", "gzip"} else codec,
            tags=json.dumps(["cpp", "compression", codec]),
            source_files=json.dumps(["main.cpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {"root": "datasets/compression", "parameter": "{domain}/{tier}", "input": "payload.bin"}
            ),
            notes=f"Loads payload.bin once (untimed), then measures {codec} compression.",
        )
    )
    decomp_meta = json.loads(
        METADATA_TEMPLATE.format(
            impl=f"lib{codec}" if codec not in {"zlib", "deflate", "gzip"} else codec,
            tags=json.dumps(["cpp", "decompression", codec]),
            source_files=json.dumps(["main.cpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {
                    "root": "datasets/fixtures/compression",
                    "parameter": "{domain}/{tier}",
                    "input": "fixture.bin",
                }
            ),
            notes=f"Loads {codec} fixture once (untimed), then measures decompression.",
        )
    )
    impl_name = {
        "zstd": "libzstd",
        "gzip": "zlib",
        "zlib": "zlib",
        "deflate": "zlib",
        "lz4": "liblz4",
        "brotli": "libbrotli",
        "snappy": "snappy",
        "bzip2": "libbz2",
        "xz": "liblzma",
        "lzma": "liblzma",
    }[codec]
    write_impl(ROOT / f"benchmarks/compression/{codec}/cpp/{impl_name}", comp_meta, cmake, comp_main)
    write_impl(ROOT / f"benchmarks/decompression/{codec}/cpp/{impl_name}", decomp_meta, cmake, decomp_main)


def compression_all() -> None:
    compression_codec(
        "zstd",
        "zstd",
        "#include <zstd.h>",
        """    const std::size_t bound = ZSTD_compressBound(data.size());
    std::vector<std::uint8_t> output(bound);
    const std::size_t written = ZSTD_compress(output.data(), bound, data.data(), data.size(), 3);
    if (ZSTD_isError(written)) {
        throw std::runtime_error("zstd compress failed");
    }
    output.resize(written);
    return output;""",
        """    const std::size_t bound = ZSTD_getFrameContentSize(data.data(), data.size());
    std::vector<std::uint8_t> output(bound == ZSTD_CONTENTSIZE_UNKNOWN ? data.size() * 4 : bound);
    const std::size_t written =
        ZSTD_decompress(output.data(), output.size(), data.data(), data.size());
    if (ZSTD_isError(written)) {
        throw std::runtime_error("zstd decompress failed");
    }
    output.resize(written);
    return output;""",
        "zstd",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(ZSTD REQUIRED libzstd)",
    )

    zlib_compress = """    uLongf bound = compressBound(static_cast<uLong>(data.size()));
    std::vector<std::uint8_t> output(bound);
    if (compress2(output.data(), &bound, data.data(), static_cast<uLong>(data.size()), Z_BEST_SPEED) != Z_OK) {
        throw std::runtime_error("zlib compress failed");
    }
    output.resize(bound);
    return output;"""

    zlib_decompress = """    std::vector<std::uint8_t> output(data.size() * 8);
    uLongf out_len = static_cast<uLongf>(output.size());
    if (uncompress(output.data(), &out_len, data.data(), static_cast<uLong>(data.size())) != Z_OK) {
        throw std::runtime_error("zlib decompress failed");
    }
    output.resize(out_len);
    return output;"""

    compression_codec(
        "zlib", "zlib", "#include <zlib.h>", zlib_compress, zlib_decompress, "z", "find_package(ZLIB REQUIRED)"
    )

    gzip_compress = """    z_stream stream {};
    if (deflateInit2(&stream, Z_BEST_SPEED, Z_DEFLATED, 15 + 16, 8, Z_DEFAULT_STRATEGY) != Z_OK) {
        throw std::runtime_error("gzip init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(deflateBound(&stream, static_cast<uLong>(data.size())));
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    if (deflate(&stream, Z_FINISH) != Z_STREAM_END) {
        deflateEnd(&stream);
        throw std::runtime_error("gzip compress failed");
    }
    output.resize(stream.total_out);
    deflateEnd(&stream);
    return output;"""

    gzip_decompress = """    z_stream stream {};
    if (inflateInit2(&stream, 15 + 16) != Z_OK) {
        throw std::runtime_error("gzip init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(data.size() * 8);
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    int code = Z_OK;
    while (code == Z_OK) {
        code = inflate(&stream, Z_NO_FLUSH);
        if (code == Z_BUF_ERROR) break;
        if (code != Z_OK && code != Z_STREAM_END) {
            inflateEnd(&stream);
            throw std::runtime_error("gzip decompress failed");
        }
        if (stream.avail_out == 0 && code != Z_STREAM_END) {
            const std::size_t offset = stream.total_out;
            output.resize(output.size() * 2);
            stream.next_out = output.data() + offset;
            stream.avail_out = static_cast<uInt>(output.size() - offset);
        }
    }
    output.resize(stream.total_out);
    inflateEnd(&stream);
    return output;"""

    compression_codec(
        "gzip", "gzip", "#include <zlib.h>", gzip_compress, gzip_decompress, "z", "find_package(ZLIB REQUIRED)"
    )

    deflate_compress = """    z_stream stream {};
    if (deflateInit(&stream, Z_BEST_SPEED) != Z_OK) {
        throw std::runtime_error("deflate init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(deflateBound(&stream, static_cast<uLong>(data.size())));
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    if (deflate(&stream, Z_FINISH) != Z_STREAM_END) {
        deflateEnd(&stream);
        throw std::runtime_error("deflate compress failed");
    }
    output.resize(stream.total_out);
    deflateEnd(&stream);
    return output;"""

    deflate_decompress = """    z_stream stream {};
    if (inflateInit(&stream) != Z_OK) {
        throw std::runtime_error("deflate init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(data.size() * 8);
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    int code = inflate(&stream, Z_FINISH);
    if (code != Z_STREAM_END) {
        inflateEnd(&stream);
        throw std::runtime_error("deflate decompress failed");
    }
    output.resize(stream.total_out);
    inflateEnd(&stream);
    return output;"""

    compression_codec(
        "deflate",
        "deflate",
        "#include <zlib.h>",
        deflate_compress,
        deflate_decompress,
        "z",
        "find_package(ZLIB REQUIRED)",
    )

    compression_codec(
        "lz4",
        "lz4",
        "#include <lz4.h>",
        """    std::vector<std::uint8_t> output(sizeof(std::uint32_t) + LZ4_compressBound(static_cast<int>(data.size())));
    const int written = LZ4_compress_default(
        reinterpret_cast<const char*>(data.data()),
        reinterpret_cast<char*>(output.data() + sizeof(std::uint32_t)),
        static_cast<int>(data.size()),
        static_cast<int>(output.size() - sizeof(std::uint32_t)));
    if (written <= 0) {
        throw std::runtime_error("lz4 compress failed");
    }
    const std::uint32_t size = static_cast<std::uint32_t>(data.size());
    std::memcpy(output.data(), &size, sizeof(size));
    output.resize(sizeof(std::uint32_t) + static_cast<std::size_t>(written));
    return output;""",
        """    if (data.size() < sizeof(std::uint32_t)) {
        throw std::runtime_error("invalid lz4 payload");
    }
    std::uint32_t original_size = 0;
    std::memcpy(&original_size, data.data(), sizeof(original_size));
    std::vector<std::uint8_t> output(original_size);
    const int written = LZ4_decompress_safe(
        reinterpret_cast<const char*>(data.data() + sizeof(std::uint32_t)),
        reinterpret_cast<char*>(output.data()),
        static_cast<int>(data.size() - sizeof(std::uint32_t)),
        static_cast<int>(output.size()));
    if (written < 0) {
        throw std::runtime_error("lz4 decompress failed");
    }
    output.resize(static_cast<std::size_t>(written));
    return output;""",
        "lz4",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(LZ4 REQUIRED liblz4)",
    )

    compression_codec(
        "snappy",
        "snappy",
        "#include <snappy.h>",
        """    std::string output;
    snappy::Compress(reinterpret_cast<const char*>(data.data()), data.size(), &output);
    return std::vector<std::uint8_t>(output.begin(), output.end());""",
        """    std::string output;
    if (!snappy::Uncompress(reinterpret_cast<const char*>(data.data()), data.size(), &output)) {
        throw std::runtime_error("snappy decompress failed");
    }
    return std::vector<std::uint8_t>(output.begin(), output.end());""",
        "snappy",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(SNAPPY REQUIRED snappy)",
    )

    compression_codec(
        "bzip2",
        "bzip2",
        "#include <bzlib.h>",
        """    const unsigned int block = 9;
    const unsigned int extra = 0;
    const unsigned int work = 30;
    std::vector<std::uint8_t> output(data.size() + 1024);
    unsigned int out_len = static_cast<unsigned int>(output.size());
    if (BZ2_bzBuffToBuffCompress(reinterpret_cast<char*>(output.data()), &out_len,
                                 reinterpret_cast<char*>(const_cast<std::uint8_t*>(data.data())),
                                 static_cast<unsigned int>(data.size()), block, extra, work) != BZ_OK) {
        throw std::runtime_error("bzip2 compress failed");
    }
    output.resize(out_len);
    return output;""",
        """    std::vector<std::uint8_t> output(data.size() * 8);
    unsigned int out_len = static_cast<unsigned int>(output.size());
    if (BZ2_bzBuffToBuffDecompress(reinterpret_cast<char*>(output.data()), &out_len,
                                   reinterpret_cast<char*>(const_cast<std::uint8_t*>(data.data())),
                                   static_cast<unsigned int>(data.size()), 0, 0) != BZ_OK) {
        throw std::runtime_error("bzip2 decompress failed");
    }
    output.resize(out_len);
    return output;""",
        "bz2",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(BZ2 REQUIRED bzip2)",
    )

    compression_codec(
        "xz",
        "xz",
        "#include <lzma.h>",
        """    lzma_stream stream = LZMA_STREAM_INIT;
    if (lzma_easy_encoder(&stream, 6, LZMA_CHECK_CRC64) != LZMA_OK) {
        throw std::runtime_error("xz init failed");
    }
    std::vector<std::uint8_t> output(data.size() + 1024);
    stream.next_in = data.data();
    stream.avail_in = data.size();
    stream.next_out = output.data();
    stream.avail_out = output.size();
    if (lzma_code(&stream, LZMA_FINISH) != LZMA_STREAM_END) {
        lzma_end(&stream);
        throw std::runtime_error("xz compress failed");
    }
    output.resize(stream.total_out);
    lzma_end(&stream);
    return output;""",
        """    lzma_stream stream = LZMA_STREAM_INIT;
    if (lzma_stream_decoder(&stream, UINT64_MAX, LZMA_CONCATENATED) != LZMA_OK) {
        throw std::runtime_error("xz init failed");
    }
    std::vector<std::uint8_t> output(data.size() * 8);
    stream.next_in = data.data();
    stream.avail_in = data.size();
    stream.next_out = output.data();
    stream.avail_out = output.size();
    if (lzma_code(&stream, LZMA_FINISH) != LZMA_STREAM_END) {
        lzma_end(&stream);
        throw std::runtime_error("xz decompress failed");
    }
    output.resize(stream.total_out);
    lzma_end(&stream);
    return output;""",
        "lzma",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(LZMA REQUIRED liblzma)",
    )

    compression_codec(
        "lzma",
        "lzma",
        "#include <lzma.h>",
        """    lzma_stream stream = LZMA_STREAM_INIT;
    lzma_options_lzma options {};
    if (lzma_lzma_encoder(&stream, &options) != LZMA_OK) {
        throw std::runtime_error("lzma init failed");
    }
    std::vector<std::uint8_t> output(data.size() + 1024);
    stream.next_in = data.data();
    stream.avail_in = data.size();
    stream.next_out = output.data();
    stream.avail_out = output.size();
    if (lzma_code(&stream, LZMA_FINISH) != LZMA_STREAM_END) {
        lzma_end(&stream);
        throw std::runtime_error("lzma compress failed");
    }
    output.resize(stream.total_out);
    lzma_end(&stream);
    return output;""",
        """    lzma_stream stream = LZMA_STREAM_INIT;
    if (lzma_stream_decoder(&stream, UINT64_MAX, LZMA_CONCATENATED) != LZMA_OK) {
        throw std::runtime_error("lzma init failed");
    }
    std::vector<std::uint8_t> output(data.size() * 8);
    stream.next_in = data.data();
    stream.avail_in = data.size();
    stream.next_out = output.data();
    stream.avail_out = output.size();
    if (lzma_code(&stream, LZMA_FINISH) != LZMA_STREAM_END) {
        lzma_end(&stream);
        throw std::runtime_error("lzma decompress failed");
    }
    output.resize(stream.total_out);
    lzma_end(&stream);
    return output;""",
        "lzma",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(LZMA REQUIRED liblzma)",
    )

    compression_codec(
        "brotli",
        "brotli",
        "#include <brotli/encode.h>\n#include <brotli/decode.h>",
        """    std::size_t bound = BrotliEncoderMaxCompressedSize(data.size());
    std::vector<std::uint8_t> output(bound);
    if (!BrotliEncoderCompress(BROTLI_DEFAULT_QUALITY, BROTLI_DEFAULT_WINDOW, BROTLI_MODE_GENERIC,
                               data.size(), data.data(), &bound, output.data())) {
        throw std::runtime_error("brotli compress failed");
    }
    output.resize(bound);
    return output;""",
        """    std::size_t decoded_size = data.size() * 8;
    std::vector<std::uint8_t> output(decoded_size);
    if (BrotliDecoderDecompress(data.size(), data.data(), &decoded_size, output.data()) !=
        BROTLI_DECODER_RESULT_SUCCESS) {
        throw std::runtime_error("brotli decompress failed");
    }
    output.resize(decoded_size);
    return output;""",
        "brotlienc brotlidec",
        "find_package(PkgConfig REQUIRED)\npkg_check_modules(BROTLI REQUIRED libbrotlienc libbrotlidec)",
    )


def protobuf_impl() -> None:
    convert_hpp = r'''#pragma once

#include <string>
#include <vector>

#include "bench/dataset.hpp"
#include "benchmark.pb.h"

namespace pb {

benchkit::Dataset decode_materialized(const std::string& spec, const std::vector<std::uint8_t>& payload);

struct Prepared {
    ::benchkit::LogDataset logs;
    ::benchkit::ProfileDataset profile;
    ::benchkit::MeshDataset mesh;
    ::benchkit::CatalogDataset catalog;
    std::string domain;
};

Prepared prepare(const benchkit::Dataset& data);
std::vector<std::uint8_t> encode(const Prepared& prepared);

}  // namespace pb
'''
    convert_cpp = r'''#include "convert.hpp"

#include <google/protobuf/util/json_util.h>

namespace pb {

namespace {

benchkit::LogDataset to_proto(const benchkit::LogDataset& data) {
    ::benchkit::LogDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    for (const auto& entry : data.entries) {
        auto* item = out.add_entries();
        item->set_timestamp(entry.timestamp);
        item->set_level(entry.level);
        item->set_message(entry.message);
        item->set_request_id(entry.request_id);
        auto* meta = item->mutable_metadata();
        meta->set_status(entry.metadata.status);
        meta->set_duration_ms(entry.metadata.duration_ms);
        meta->set_bytes_sent(entry.metadata.bytes_sent);
        meta->set_user_agent(entry.metadata.user_agent);
        meta->set_remote_addr(entry.metadata.remote_addr);
    }
    return out;
}

benchkit::LogDataset from_proto(const ::benchkit::LogDataset& data) {
    benchkit::LogDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.entries.reserve(static_cast<std::size_t>(data.entries_size()));
    for (const auto& entry : data.entries()) {
        benchkit::LogEntry item;
        item.timestamp = entry.timestamp();
        item.level = entry.level();
        item.message = entry.message();
        item.request_id = entry.request_id();
        item.metadata.status = static_cast<std::uint16_t>(entry.metadata().status());
        item.metadata.duration_ms = entry.metadata().duration_ms();
        item.metadata.bytes_sent = entry.metadata().bytes_sent();
        item.metadata.user_agent = entry.metadata().user_agent();
        item.metadata.remote_addr = entry.metadata().remote_addr();
        out.entries.push_back(std::move(item));
    }
    return out;
}

::benchkit::ProfileDataset to_proto(const benchkit::ProfileDataset& data) {
    ::benchkit::ProfileDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    for (const auto& profile : data.profiles) {
        auto* item = out.add_profiles();
        item->set_id(profile.id);
        item->set_name(profile.name);
        item->set_email(profile.email);
        item->set_active(profile.active);
        for (const auto& tag : profile.tags) {
            item->add_tags(tag);
        }
        item->mutable_preferences()->set_locale(profile.preferences.locale);
        item->mutable_preferences()->set_newsletter(profile.preferences.newsletter);
        item->mutable_preferences()->set_theme(profile.preferences.theme);
        item->mutable_address()->set_city(profile.address.city);
        item->mutable_address()->set_postal_code(profile.address.postal_code);
        item->mutable_address()->set_country(profile.address.country);
    }
    return out;
}

benchkit::ProfileDataset from_proto(const ::benchkit::ProfileDataset& data) {
    benchkit::ProfileDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.profiles.reserve(static_cast<std::size_t>(data.profiles_size()));
    for (const auto& profile : data.profiles()) {
        benchkit::Profile item;
        item.id = profile.id();
        item.name = profile.name();
        item.email = profile.email();
        item.active = profile.active();
        item.tags.reserve(static_cast<std::size_t>(profile.tags_size()));
        for (const auto& tag : profile.tags()) {
            item.tags.push_back(tag);
        }
        item.preferences.locale = profile.preferences().locale();
        item.preferences.newsletter = profile.preferences().newsletter();
        item.preferences.theme = profile.preferences().theme();
        item.address.city = profile.address().city();
        item.address.postal_code = profile.address().postal_code();
        item.address.country = profile.address().country();
        out.profiles.push_back(std::move(item));
    }
    return out;
}

::benchkit::MeshDataset to_proto(const benchkit::MeshDataset& data) {
    ::benchkit::MeshDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    out.set_name(data.name);
    for (const auto& vertex : data.vertices) {
        auto* item = out.add_vertices();
        item->set_x(vertex.x);
        item->set_y(vertex.y);
        item->set_z(vertex.z);
        item->set_nx(vertex.nx);
        item->set_ny(vertex.ny);
        item->set_nz(vertex.nz);
    }
    for (const auto index : data.indices) {
        out.add_indices(index);
    }
    return out;
}

benchkit::MeshDataset from_proto(const ::benchkit::MeshDataset& data) {
    benchkit::MeshDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.name = data.name();
    out.vertices.reserve(static_cast<std::size_t>(data.vertices_size()));
    for (const auto& vertex : data.vertices()) {
        out.vertices.push_back(
            benchkit::Vertex{vertex.x(), vertex.y(), vertex.z(), vertex.nx(), vertex.ny(), vertex.nz()});
    }
    out.indices.reserve(static_cast<std::size_t>(data.indices_size()));
    for (const auto index : data.indices()) {
        out.indices.push_back(index);
    }
    return out;
}

::benchkit::CatalogDataset to_proto(const benchkit::CatalogDataset& data) {
    ::benchkit::CatalogDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    for (const auto& product : data.products) {
        auto* item = out.add_products();
        item->set_sku(product.sku);
        item->set_name(product.name);
        item->set_price_cents(product.price_cents);
        item->set_currency(product.currency);
        item->set_in_stock(product.in_stock);
        for (const auto& tag : product.tags) {
            item->add_tags(tag);
        }
        auto* attrs = item->mutable_attributes();
        for (const auto& [key, value] : product.attributes) {
            (*attrs)[key] = value;
        }
    }
    return out;
}

benchkit::CatalogDataset from_proto(const ::benchkit::CatalogDataset& data) {
    benchkit::CatalogDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.products.reserve(static_cast<std::size_t>(data.products_size()));
    for (const auto& product : data.products()) {
        benchkit::Product item;
        item.sku = product.sku();
        item.name = product.name();
        item.price_cents = product.price_cents();
        item.currency = product.currency();
        item.in_stock = product.in_stock();
        item.tags.reserve(static_cast<std::size_t>(product.tags_size()));
        for (const auto& tag : product.tags()) {
            item.tags.push_back(tag);
        }
        for (const auto& [key, value] : product.attributes()) {
            item.attributes.emplace(key, value);
        }
        out.products.push_back(std::move(item));
    }
    return out;
}

}  // namespace

Prepared prepare(const benchkit::Dataset& data) {
    Prepared prepared;
    std::visit(
        [&](const auto& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, benchkit::LogDataset>) {
                prepared.domain = "logs";
                prepared.logs = to_proto(value);
            } else if constexpr (std::is_same_v<T, benchkit::ProfileDataset>) {
                prepared.domain = "profile";
                prepared.profile = to_proto(value);
            } else if constexpr (std::is_same_v<T, benchkit::MeshDataset>) {
                prepared.domain = "mesh";
                prepared.mesh = to_proto(value);
            } else if constexpr (std::is_same_v<T, benchkit::CatalogDataset>) {
                prepared.domain = "catalog";
                prepared.catalog = to_proto(value);
            }
        },
        data);
    return prepared;
}

std::vector<std::uint8_t> encode(const Prepared& prepared) {
    std::string bytes;
    if (prepared.domain == "logs") {
        prepared.logs.SerializeToString(&bytes);
    } else if (prepared.domain == "profile") {
        prepared.profile.SerializeToString(&bytes);
    } else if (prepared.domain == "mesh") {
        prepared.mesh.SerializeToString(&bytes);
    } else if (prepared.domain == "catalog") {
        prepared.catalog.SerializeToString(&bytes);
    }
    return std::vector<std::uint8_t>(bytes.begin(), bytes.end());
}

benchkit::Dataset decode_materialized(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") {
        ::benchkit::LogDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    if (domain == "profile") {
        ::benchkit::ProfileDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    if (domain == "mesh") {
        ::benchkit::MeshDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    if (domain == "catalog") {
        ::benchkit::CatalogDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    throw std::runtime_error("unknown domain");
}

}  // namespace pb
'''
    ser_main = r'''#include <iostream>
#include <string>

#include "bench/dataset.hpp"
#include "bench/timing.hpp"
#include "convert.hpp"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const pb::Prepared prepared = pb::prepare(data);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_with_setup(load_seconds, prepared, pb::encode);
    benchkit::print_result(result);
    return 0;
}
'''
    deser_main = r'''#include <iostream>
#include <string>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include "convert.hpp"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_fixture_bytes("prost", spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload,
        [&](const std::vector<std::uint8_t>& bytes) { return pb::decode_materialized(spec, bytes); });
    benchkit::print_result(result);
    return 0;
}
'''
    cmake = f'''cmake_minimum_required(VERSION 3.16)
project(protobuf_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Protobuf REQUIRED)
set(SCHEMA "{SCHEMA}/benchmark.proto")
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${{SCHEMA}})

add_executable(bench main.cpp convert.cpp ${{PROTO_SRCS}})
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}" ${{CMAKE_CURRENT_BINARY_DIR}})
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE protobuf::libprotobuf z)
'''
    ser_meta = json.loads(
        METADATA_TEMPLATE.format(
            impl="protobuf-cpp",
            tags=json.dumps(["cpp", "protobuf", "binary"]),
            source_files=json.dumps(["main.cpp", "convert.cpp", "convert.hpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {"root": "datasets/shared", "parameter": "{domain}/{tier}", "input": "canonical.json"}
            ),
            notes="Canonical dataset to protobuf message (untimed), then timed SerializeToString.",
        )
    )
    deser_meta = json.loads(
        METADATA_TEMPLATE.format(
            impl="protobuf-cpp",
            tags=json.dumps(["cpp", "protobuf", "deserialize"]),
            source_files=json.dumps(["main.cpp", "convert.cpp", "convert.hpp", "CMakeLists.txt"]),
            dataset=json.dumps(
                {"root": "datasets/fixtures", "parameter": "{domain}/{tier}", "input": "fixture.bin"}
            ),
            notes="Loads prost fixture once (untimed), then timed ParseFromArray + full materialization.",
        )
    )
    extra = {"convert.hpp": convert_hpp, "convert.cpp": convert_cpp}
    write_impl(
        ROOT / "benchmarks/serialization/protobuf/cpp/protobuf-cpp",
        ser_meta,
        cmake,
        ser_main,
        extra,
    )
    write_impl(
        ROOT / "benchmarks/deserialization/protobuf/cpp/protobuf-cpp",
        deser_meta,
        cmake,
        deser_main,
        extra,
    )


def main() -> None:
    json_serialize()
    json_deserialize()
    msgpack_serialize()
    protobuf_impl()
    compression_all()
    print("Scaffolded C++ benchmarks")


if __name__ == "__main__":
    main()
