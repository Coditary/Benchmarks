#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <brotli/encode.h>
#include <brotli/decode.h>

namespace {

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    std::size_t decoded_size = data.size() * 8;
    std::vector<std::uint8_t> output(decoded_size);
    if (BrotliDecoderDecompress(data.size(), data.data(), &decoded_size, output.data()) !=
        BROTLI_DECODER_RESULT_SUCCESS) {
        throw std::runtime_error("brotli decompress failed");
    }
    output.resize(decoded_size);
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
