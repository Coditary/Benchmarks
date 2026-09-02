#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
extern "C" {
#include <libdeflate.h>
}

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    struct libdeflate_compressor* compressor = libdeflate_alloc_compressor(6);
    if (compressor == nullptr) {
        throw std::runtime_error("libdeflate compress init failed");
    }
    const std::size_t bound = libdeflate_deflate_compress_bound(compressor, data.size());
    std::vector<std::uint8_t> output(bound);
    const std::size_t written = libdeflate_deflate_compress(
        compressor,
        data.data(),
        data.size(),
        output.data(),
        output.size());
    libdeflate_free_compressor(compressor);
    if (written == 0) {
        throw std::runtime_error("libdeflate compress failed");
    }
    output.resize(written);
    return output;
}

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    struct libdeflate_decompressor* decompressor = libdeflate_alloc_decompressor();
    if (decompressor == nullptr) {
        throw std::runtime_error("libdeflate decompress init failed");
    }
    std::size_t capacity = std::max<std::size_t>(data.size() * 4, 64);
    constexpr std::size_t kMaxCapacity = 256ULL * 1024 * 1024;
    std::vector<std::uint8_t> output;
    while (capacity <= kMaxCapacity) {
        output.assign(capacity, 0);
        std::size_t actual_out = 0;
        const enum libdeflate_result result = libdeflate_deflate_decompress(
            decompressor,
            data.data(),
            data.size(),
            output.data(),
            output.size(),
            &actual_out);
        if (result == LIBDEFLATE_SUCCESS) {
            libdeflate_free_decompressor(decompressor);
            output.resize(actual_out);
            return output;
        }
        if (result == LIBDEFLATE_INSUFFICIENT_SPACE) {
            capacity *= 2;
            continue;
        }
        libdeflate_free_decompressor(decompressor);
        throw std::runtime_error("libdeflate decompress failed");
    }
    libdeflate_free_decompressor(decompressor);
    throw std::runtime_error("libdeflate decompress output too large");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> uncompressed = benchkit::load_compression_payload(spec);
    const std::vector<std::uint8_t> payload = compress_payload(uncompressed);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, decompress_payload);
    benchkit::print_result(result);
    return 0;
}
