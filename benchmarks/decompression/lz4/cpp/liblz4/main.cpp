#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <lz4.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    std::vector<std::uint8_t> output(sizeof(std::uint32_t) + LZ4_compressBound(static_cast<int>(data.size())));
    const int written = LZ4_compress_default(
        reinterpret_cast<const char*>(data.data()),
        reinterpret_cast<char*>(output.data() + sizeof(std::uint32_t)),
        static_cast<int>(data.size()),
        static_cast<int>(output.size() - sizeof(std::uint32_t)));
    if (written <= 0) {
        throw std::runtime_error("lz4 compress failed");
    }
    const std::uint32_t size = static_cast<std::uint32_t>(data.size());
    std::memcpy(output.data(), &size, sizeof(size));
    output.resize(sizeof(std::uint32_t) + static_cast<std::size_t>(written));
    return output;
}

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    if (data.size() < sizeof(std::uint32_t)) {
        throw std::runtime_error("invalid lz4 payload");
    }
    std::uint32_t original_size = 0;
    std::memcpy(&original_size, data.data(), sizeof(original_size));
    std::vector<std::uint8_t> output(original_size);
    const int written = LZ4_decompress_safe(
        reinterpret_cast<const char*>(data.data() + sizeof(std::uint32_t)),
        reinterpret_cast<char*>(output.data()),
        static_cast<int>(data.size() - sizeof(std::uint32_t)),
        static_cast<int>(output.size()));
    if (written < 0) {
        throw std::runtime_error("lz4 decompress failed");
    }
    output.resize(static_cast<std::size_t>(written));
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
