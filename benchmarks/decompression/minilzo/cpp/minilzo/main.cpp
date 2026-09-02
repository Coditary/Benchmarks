#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include "minilzo.h"

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    if (lzo_init() != LZO_E_OK) {
        throw std::runtime_error("minilzo init failed");
    }
    std::vector<std::uint8_t> output(sizeof(std::uint32_t) + data.size() + data.size() / 16 + 64 + 3);
    lzo_uint written = static_cast<lzo_uint>(output.size() - sizeof(std::uint32_t));
    std::vector<unsigned char> workmem(LZO1X_1_MEM_COMPRESS);
    if (lzo1x_1_compress(
            data.data(),
            static_cast<lzo_uint>(data.size()),
            output.data() + sizeof(std::uint32_t),
            &written,
            workmem.data()) != LZO_E_OK) {
        throw std::runtime_error("minilzo compress failed");
    }
    const std::uint32_t size = static_cast<std::uint32_t>(data.size());
    std::memcpy(output.data(), &size, sizeof(size));
    output.resize(sizeof(std::uint32_t) + static_cast<std::size_t>(written));
    return output;
}

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    if (data.size() < sizeof(std::uint32_t)) {
        throw std::runtime_error("invalid minilzo payload");
    }
    std::uint32_t original_size = 0;
    std::memcpy(&original_size, data.data(), sizeof(original_size));
    std::vector<std::uint8_t> output(original_size);
    lzo_uint written = static_cast<lzo_uint>(output.size());
    if (lzo1x_decompress(
            data.data() + sizeof(std::uint32_t),
            static_cast<lzo_uint>(data.size() - sizeof(std::uint32_t)),
            output.data(),
            &written,
            nullptr) != LZO_E_OK || written != original_size) {
        throw std::runtime_error("minilzo decompress failed");
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
