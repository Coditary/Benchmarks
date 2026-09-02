#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <zlib.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    z_stream stream {};
    if (deflateInit2(&stream, Z_BEST_SPEED, Z_DEFLATED, 15 + 16, 8, Z_DEFAULT_STRATEGY) != Z_OK) {
        throw std::runtime_error("gzip init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(deflateBound(&stream, static_cast<uLong>(data.size())));
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    if (deflate(&stream, Z_FINISH) != Z_STREAM_END) {
        deflateEnd(&stream);
        throw std::runtime_error("gzip compress failed");
    }
    output.resize(stream.total_out);
    deflateEnd(&stream);
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
