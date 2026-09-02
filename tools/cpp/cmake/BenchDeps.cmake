include_guard(GLOBAL)

function(bench_fetch_nlohmann_json)
    if(TARGET nlohmann_json::nlohmann_json)
        return()
    endif()
    find_package(nlohmann_json 3.2.0 QUIET)
    if(nlohmann_json_FOUND)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        nlohmann_json
        URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(nlohmann_json)
endfunction()

function(bench_link_z target)
    find_package(ZLIB REQUIRED)
    if(TARGET ZLIB::ZLIB)
        target_link_libraries(${target} PRIVATE ZLIB::ZLIB)
    else()
        target_link_libraries(${target} PRIVATE z)
    endif()
endfunction()

function(bench_link_zstd target)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(ZSTD REQUIRED IMPORTED_TARGET libzstd)
    target_link_libraries(${target} PRIVATE PkgConfig::ZSTD)
endfunction()

function(bench_link_lz4 target)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(LZ4 REQUIRED IMPORTED_TARGET liblz4)
    target_link_libraries(${target} PRIVATE PkgConfig::LZ4)
endfunction()

function(bench_link_snappy target)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SNAPPY REQUIRED IMPORTED_TARGET snappy)
    target_link_libraries(${target} PRIVATE PkgConfig::SNAPPY)
endfunction()

function(bench_link_bz2 target)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(BZ2 REQUIRED IMPORTED_TARGET bzip2)
    target_link_libraries(${target} PRIVATE PkgConfig::BZ2)
endfunction()

function(bench_link_lzma target)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(LZMA REQUIRED IMPORTED_TARGET liblzma)
    target_link_libraries(${target} PRIVATE PkgConfig::LZMA)
endfunction()

function(bench_link_brotli target)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(BROTLIENC REQUIRED IMPORTED_TARGET libbrotlienc)
    pkg_check_modules(BROTLIDEC REQUIRED IMPORTED_TARGET libbrotlidec)
    target_link_libraries(${target} PRIVATE PkgConfig::BROTLIENC PkgConfig::BROTLIDEC)
endfunction()

function(bench_fetch_flatbuffers)
    if(TARGET flatbuffers)
        return()
    endif()
    find_package(flatbuffers CONFIG QUIET)
    if(flatbuffers_FOUND)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        flatbuffers
        URL https://github.com/google/flatbuffers/archive/refs/tags/v24.12.23.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    set(FLATBUFFERS_BUILD_FLATC OFF CACHE BOOL "" FORCE)
    set(FLATBUFFERS_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(FLATBUFFERS_INSTALL OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(flatbuffers)
endfunction()

function(bench_link_flatbuffers target)
    bench_fetch_flatbuffers()
    target_link_libraries(${target} PRIVATE flatbuffers)
endfunction()

function(bench_link_capnp target)
    find_package(CapnProto REQUIRED)
    target_link_libraries(${target} PRIVATE CapnProto::capnp CapnProto::kj)
endfunction()

function(bench_fetch_msgpack)
    if(TARGET msgpack-cxx)
        return()
    endif()
    find_path(MSGPACK_INCLUDE_DIR msgpack.hpp)
    if(MSGPACK_INCLUDE_DIR)
        add_library(msgpack-cxx INTERFACE)
        target_include_directories(msgpack-cxx INTERFACE ${MSGPACK_INCLUDE_DIR})
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        msgpack
        URL https://github.com/msgpack/msgpack-c/releases/download/cpp-6.1.0/msgpack-cxx-6.1.0.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(msgpack)
    if(NOT TARGET msgpack-cxx)
        add_library(msgpack-cxx INTERFACE)
        target_include_directories(msgpack-cxx INTERFACE ${msgpack_SOURCE_DIR}/include)
    endif()
endfunction()

function(bench_find_msgpack target)
    bench_fetch_msgpack()
    target_link_libraries(${target} PRIVATE msgpack-cxx)
endfunction()

function(bench_fetch_yaml_cpp)
    if(TARGET yaml-cpp)
        return()
    endif()
    find_package(yaml-cpp QUIET)
    if(yaml-cpp_FOUND)
        return()
    endif()
    include(FetchContent)
    set(_bench_policy_minimum "${CMAKE_POLICY_VERSION_MINIMUM}")
    if(CMAKE_VERSION VERSION_GREATER_EQUAL "3.26")
        set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
    endif()
    FetchContent_Declare(
        yaml-cpp
        URL https://github.com/jbeder/yaml-cpp/archive/refs/tags/yaml-cpp-0.9.0.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(yaml-cpp)
    set(CMAKE_POLICY_VERSION_MINIMUM "${_bench_policy_minimum}")
endfunction()

function(bench_link_yaml_cpp target)
    bench_fetch_yaml_cpp()
    if(TARGET yaml-cpp)
        target_link_libraries(${target} PRIVATE yaml-cpp)
    else()
        target_link_libraries(${target} PRIVATE yaml-cpp::yaml-cpp)
    endif()
endfunction()

function(bench_fetch_tomlplusplus)
    if(TARGET tomlplusplus::tomlplusplus)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        tomlplusplus
        URL https://github.com/marzer/tomlplusplus/archive/refs/tags/v3.4.0.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(tomlplusplus)
endfunction()

function(bench_link_tomlplusplus target)
    bench_fetch_tomlplusplus()
    target_link_libraries(${target} PRIVATE tomlplusplus::tomlplusplus)
endfunction()

function(bench_fetch_pugixml)
    if(TARGET pugixml::static)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        pugixml
        URL https://github.com/zeux/pugixml/archive/refs/tags/v1.14.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(pugixml)
endfunction()

function(bench_link_pugixml target)
    bench_fetch_pugixml()
    target_link_libraries(${target} PRIVATE pugixml::static)
endfunction()

function(bench_fetch_cjson)
    if(TARGET cjson)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        cjson
        URL https://github.com/DaveGamble/cJSON/archive/refs/tags/v1.7.18.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    set(ENABLE_CJSON_TEST OFF CACHE BOOL "" FORCE)
    set(ENABLE_CJSON_UTILS OFF CACHE BOOL "" FORCE)
    set(ENABLE_CJSON_UNINSTALL OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(cjson)
    set(BENCH_CJSON_SOURCE_DIR "${cjson_SOURCE_DIR}" CACHE INTERNAL "")
endfunction()

function(bench_link_cjson target)
    bench_fetch_cjson()
    target_link_libraries(${target} PRIVATE cjson)
    if(BENCH_CJSON_SOURCE_DIR)
        target_include_directories(${target} PRIVATE "${BENCH_CJSON_SOURCE_DIR}")
    endif()
endfunction()

function(bench_fetch_hjson_cpp)
    if(TARGET hjson-cpp)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        hjson_cpp
        URL https://github.com/hjson/hjson-cpp/archive/refs/tags/2.4.1.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(hjson_cpp)
    if(NOT TARGET hjson-cpp AND TARGET hjson)
        add_library(hjson-cpp ALIAS hjson)
    endif()
endfunction()

function(bench_link_hjson_cpp target)
    bench_fetch_hjson_cpp()
    if(TARGET hjson-cpp)
        target_link_libraries(${target} PRIVATE hjson-cpp)
    elseif(TARGET hjson)
        target_link_libraries(${target} PRIVATE hjson)
    else()
        message(FATAL_ERROR "hjson-cpp target not found after FetchContent")
    endif()
    if(DEFINED hjson_cpp_SOURCE_DIR)
        target_include_directories(${target} PRIVATE "${hjson_cpp_SOURCE_DIR}/include")
    endif()
endfunction()

function(bench_fetch_libucl)
    if(TARGET libucl)
        return()
    endif()
    include(FetchContent)
    FetchContent_Declare(
        libucl
        URL https://github.com/vstakhov/libucl/archive/refs/tags/0.9.2.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(libucl)
endfunction()

function(bench_link_ucl target)
    bench_fetch_libucl()
    if(TARGET libucl)
        target_link_libraries(${target} PRIVATE libucl)
    elseif(TARGET ucl)
        target_link_libraries(${target} PRIVATE ucl)
    else()
        message(FATAL_ERROR "libucl target not found after FetchContent")
    endif()
endfunction()

function(bench_link_nlohmann_json target)
    bench_fetch_nlohmann_json()
    target_link_libraries(${target} PRIVATE nlohmann_json::nlohmann_json)
endfunction()
