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

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_compression_payload(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_with_setup(load_seconds, payload, compress_payload);
    benchkit::print_result(result);
    return 0;
}
