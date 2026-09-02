cmake_minimum_required(VERSION 3.16)
project(decompression_zlib-ng LANGUAGES CXX C)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(bench main.cpp)
target_include_directories(bench PRIVATE "../../../../../tools/cpp/bench-support/include")
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
include("../../../../../tools/cpp/cmake/BenchDeps.cmake")
bench_link_zlib_ng(bench)

