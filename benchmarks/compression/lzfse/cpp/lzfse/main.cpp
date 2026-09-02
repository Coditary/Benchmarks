#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
extern "C" {
#include <lzfse.h>
}

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    std::vector<std::uint8_t> output(data.size() + 12);
    const std::size_t written = lzfse_encode_buffer(
        output.data(),
        output.size(),
        data.data(),
        data.size(),
        nullptr);
    if (written == 0) {
        throw std::runtime_error("lzfse compress failed");
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
