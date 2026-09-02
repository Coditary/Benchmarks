#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <zlib.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    uLongf bound = compressBound(static_cast<uLong>(data.size()));
    std::vector<std::uint8_t> output(bound);
    if (compress2(output.data(), &bound, data.data(), static_cast<uLong>(data.size()), Z_BEST_SPEED) != Z_OK) {
        throw std::runtime_error("zlib compress failed");
    }
    output.resize(bound);
    return output;
}

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    std::vector<std::uint8_t> output(data.size() * 8);
    uLongf out_len = static_cast<uLongf>(output.size());
    if (uncompress(output.data(), &out_len, data.data(), static_cast<uLong>(data.size())) != Z_OK) {
        throw std::runtime_error("zlib decompress failed");
    }
    output.resize(out_len);
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
    const std::vector<std::uint8_t> uncompressed = benchkit::load_compression_payload(spec);
    const std::vector<std::uint8_t> payload = compress_payload(uncompressed);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, decompress_payload);
    benchkit::print_result(result);
    return 0;
}
