cmake_minimum_required(VERSION 3.16)
project(capnp_cpp_serialize LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include("../../../../../tools/cpp/cmake/BenchDeps.cmake")
bench_fetch_nlohmann_json()

add_executable(bench main.cpp serialize.cpp generated/benchmark.capnp.c++)
target_include_directories(bench PRIVATE
    "../../../../../tools/cpp/bench-support/include"
    "${CMAKE_CURRENT_SOURCE_DIR}/generated"
)
target_compile_options(bench PRIVATE -O3 -DNDEBUG)
target_link_libraries(bench PRIVATE nlohmann_json::nlohmann_json)
bench_link_capnp(bench)
bench_link_z(bench)
