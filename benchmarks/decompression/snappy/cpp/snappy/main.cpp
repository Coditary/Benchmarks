#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <snappy.h>

namespace {

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    std::string output;
    if (!snappy::Uncompress(reinterpret_cast<const char*>(data.data()), data.size(), &output)) {
        throw std::runtime_error("snappy decompress failed");
    }
    return std::vector<std::uint8_t>(output.begin(), output.end());
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
