#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
extern "C" {
#include "zopfli.h"
#include <libdeflate.h>
}

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    ZopfliOptions options;
    ZopfliInitOptions(&options);
    unsigned char* out = nullptr;
    std::size_t outsize = 0;
    ZopfliCompress(
        &options,
        ZOPFLI_FORMAT_DEFLATE,
        data.data(),
        data.size(),
        &out,
        &outsize);
    if (out == nullptr || outsize == 0) {
        throw std::runtime_error("zopfli compress failed");
    }
    std::vector<std::uint8_t> output(out, out + outsize);
    std::free(out);
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
