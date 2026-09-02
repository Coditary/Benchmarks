#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <bzlib.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    const unsigned int block = 9;
    const unsigned int extra = 0;
    const unsigned int work = 30;
    std::vector<std::uint8_t> output(data.size() + 1024);
    unsigned int out_len = static_cast<unsigned int>(output.size());
    if (BZ2_bzBuffToBuffCompress(reinterpret_cast<char*>(output.data()), &out_len,
                                 reinterpret_cast<char*>(const_cast<std::uint8_t*>(data.data())),
                                 static_cast<unsigned int>(data.size()), block, extra, work) != BZ_OK) {
        throw std::runtime_error("bzip2 compress failed");
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
    const std::vector<std::uint8_t> payload = benchkit::load_compression_payload(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_with_setup(load_seconds, payload, compress_payload);
    benchkit::print_result(result);
    return 0;
}
