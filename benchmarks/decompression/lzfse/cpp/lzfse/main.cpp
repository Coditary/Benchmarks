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

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    std::size_t capacity = std::max<std::size_t>(data.size() * 4, 64);
    constexpr std::size_t kMaxCapacity = 256ULL * 1024 * 1024;
    std::vector<std::uint8_t> output;
    while (capacity <= kMaxCapacity) {
        output.assign(capacity, 0);
        const std::size_t written = lzfse_decode_buffer(
            output.data(),
            output.size(),
            data.data(),
            data.size(),
            nullptr);
        if (written == 0) {
            throw std::runtime_error("lzfse decompress failed");
        }
        if (written < capacity) {
            output.resize(written);
            return output;
        }
        capacity *= 2;
    }
    throw std::runtime_error("lzfse decompress output too large");
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
