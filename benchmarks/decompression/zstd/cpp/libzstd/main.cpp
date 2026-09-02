#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <zstd.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    const std::size_t bound = ZSTD_compressBound(data.size());
    std::vector<std::uint8_t> output(bound);
    const std::size_t written = ZSTD_compress(output.data(), bound, data.data(), data.size(), 3);
    if (ZSTD_isError(written)) {
        throw std::runtime_error("zstd compress failed");
    }
    output.resize(written);
    return output;
}

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    const std::size_t bound = ZSTD_getFrameContentSize(data.data(), data.size());
    std::vector<std::uint8_t> output(bound == ZSTD_CONTENTSIZE_UNKNOWN ? data.size() * 4 : bound);
    const std::size_t written =
        ZSTD_decompress(output.data(), output.size(), data.data(), data.size());
    if (ZSTD_isError(written)) {
        throw std::runtime_error("zstd decompress failed");
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
    const std::vector<std::uint8_t> uncompressed = benchkit::load_compression_payload(spec);
    const std::vector<std::uint8_t> payload = compress_payload(uncompressed);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, decompress_payload);
    benchkit::print_result(result);
    return 0;
}
