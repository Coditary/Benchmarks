#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <lzma.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    lzma_stream stream = LZMA_STREAM_INIT;
    lzma_options_lzma options {};
    if (lzma_lzma_preset(&options, LZMA_PRESET_DEFAULT) != LZMA_OK) {
        throw std::runtime_error("lzma preset failed");
    }
    if (lzma_alone_encoder(&stream, &options) != LZMA_OK) {
        throw std::runtime_error("lzma init failed");
    }
    std::vector<std::uint8_t> output(data.size() + 1024);
    stream.next_in = data.data();
    stream.avail_in = data.size();
    stream.next_out = output.data();
    stream.avail_out = output.size();
    if (lzma_code(&stream, LZMA_FINISH) != LZMA_STREAM_END) {
        lzma_end(&stream);
        throw std::runtime_error("lzma compress failed");
    }
    output.resize(stream.total_out);
    lzma_end(&stream);
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
