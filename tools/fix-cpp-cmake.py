#!/usr/bin/env python3
"""Fix generated C++ benchmark CMake files to use shared BenchDeps."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CMAKE_DIR = '../../../../../tools/cpp/cmake'
BENCH_SUPPORT = '../../../../../tools/cpp/bench-support/include'

TEMPLATES = {
    'json': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("{CMAKE_DIR}/BenchDeps.cmake")
bench_fetch_nlohmann_json()
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_z(bench)
''',
    'msgpack': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("{CMAKE_DIR}/BenchDeps.cmake")
bench_fetch_nlohmann_json()
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_find_msgpack(bench)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_z(bench)
''',
    'protobuf': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Protobuf REQUIRED)
set(SCHEMA "../../../../../datasets/shared/schemas/benchmark.proto")
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${{SCHEMA}})
add_executable(bench main.cpp convert.cpp ${{PROTO_SRCS}})
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}" ${{CMAKE_CURRENT_BINARY_DIR}})
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE protobuf::libprotobuf)
bench_link_z(bench)
include("{CMAKE_DIR}/BenchDeps.cmake")
''',
    'flatbuffers': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("{CMAKE_DIR}/BenchDeps.cmake")
bench_fetch_nlohmann_json()
bench_fetch_flatbuffers()
add_executable(bench main.cpp serialize.cpp)
target_include_directories(bench PRIVATE
    "{BENCH_SUPPORT}"
    "${{CMAKE_CURRENT_SOURCE_DIR}}/generated"
)
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_flatbuffers(bench)
bench_link_z(bench)
''',
    'capnp': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("{CMAKE_DIR}/BenchDeps.cmake")
bench_fetch_nlohmann_json()
add_executable(bench main.cpp serialize.cpp generated/benchmark.capnp.c++)
target_include_directories(bench PRIVATE
    "{BENCH_SUPPORT}"
    "${{CMAKE_CURRENT_SOURCE_DIR}}/generated"
)
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_capnp(bench)
bench_link_z(bench)
''',
    'flexbuffers': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include("{CMAKE_DIR}/BenchDeps.cmake")
bench_fetch_nlohmann_json()
bench_fetch_flatbuffers()
add_executable(bench main.cpp serialize.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_flatbuffers(bench)
bench_link_z(bench)
''',
    'zstd': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_zstd(bench)
bench_link_z(bench)
''',
    'zlib': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_z(bench)
''',
    'lz4': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_lz4(bench)
bench_link_z(bench)
''',
    'snappy': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_snappy(bench)
bench_link_z(bench)
''',
    'bzip2': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_bz2(bench)
bench_link_z(bench)
''',
    'lzma': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_lzma(bench)
bench_link_z(bench)
''',
    'brotli': f'''cmake_minimum_required(VERSION 3.16)
project(cpp_bench LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
include("{CMAKE_DIR}/BenchDeps.cmake")
add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "{BENCH_SUPPORT}")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
bench_link_brotli(bench)
bench_link_z(bench)
''',
}

MAPPING = {
    'serialization/json/cpp/nlohmann-json': 'json',
    'deserialization/json/cpp/nlohmann-json': 'json',
    'serialization/messagepack/cpp/msgpack-cxx': 'msgpack',
    'deserialization/messagepack/cpp/msgpack-cxx': 'msgpack',
    'serialization/protobuf/cpp/protobuf-cpp': 'protobuf',
    'deserialization/protobuf/cpp/protobuf-cpp': 'protobuf',
    'serialization/flatbuffers/cpp/flatbuffers-cpp': 'flatbuffers',
    'serialization/capnp/cpp/capnp-cpp': 'capnp',
    'serialization/flexbuffers/cpp/flexbuffers-cpp': 'flexbuffers',
    'compression/zstd/cpp/libzstd': 'zstd',
    'decompression/zstd/cpp/libzstd': 'zstd',
    'compression/zlib/cpp/zlib': 'zlib',
    'decompression/zlib/cpp/zlib': 'zlib',
    'compression/gzip/cpp/zlib': 'zlib',
    'decompression/gzip/cpp/zlib': 'zlib',
    'compression/deflate/cpp/zlib': 'zlib',
    'decompression/deflate/cpp/zlib': 'zlib',
    'compression/lz4/cpp/liblz4': 'lz4',
    'decompression/lz4/cpp/liblz4': 'lz4',
    'compression/snappy/cpp/snappy': 'snappy',
    'decompression/snappy/cpp/snappy': 'snappy',
    'compression/bzip2/cpp/libbz2': 'bzip2',
    'decompression/bzip2/cpp/libbz2': 'bzip2',
    'compression/xz/cpp/liblzma': 'lzma',
    'decompression/xz/cpp/liblzma': 'lzma',
    'compression/lzma/cpp/liblzma': 'lzma',
    'decompression/lzma/cpp/liblzma': 'lzma',
    'compression/brotli/cpp/libbrotli': 'brotli',
    'decompression/brotli/cpp/libbrotli': 'brotli',
}

for rel, kind in MAPPING.items():
    path = ROOT / 'benchmarks' / rel / 'CMakeLists.txt'
    path.write_text(TEMPLATES[kind])
    print('updated', path)
