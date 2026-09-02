#include <cstring>
#include <iostream>
#include <vector>

#include "bench/paths.hpp"
#include "bench/timing.hpp"
#include <zlib.h>

namespace {

std::vector<std::uint8_t> compress_payload(const std::vector<std::uint8_t>& data) {
    z_stream stream {};
    if (deflateInit(&stream, Z_BEST_SPEED) != Z_OK) {
        throw std::runtime_error("deflate init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(deflateBound(&stream, static_cast<uLong>(data.size())));
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    if (deflate(&stream, Z_FINISH) != Z_STREAM_END) {
        deflateEnd(&stream);
        throw std::runtime_error("deflate compress failed");
    }
    output.resize(stream.total_out);
    deflateEnd(&stream);
    return output;
}

std::vector<std::uint8_t> decompress_payload(const std::vector<std::uint8_t>& data) {
    z_stream stream {};
    if (inflateInit(&stream) != Z_OK) {
        throw std::runtime_error("deflate init failed");
    }
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(data.data()));
    stream.avail_in = static_cast<uInt>(data.size());
    std::vector<std::uint8_t> output(data.size() * 8);
    stream.next_out = output.data();
    stream.avail_out = static_cast<uInt>(output.size());
    int code = inflate(&stream, Z_FINISH);
    if (code != Z_STREAM_END) {
        inflateEnd(&stream);
        throw std::runtime_error("deflate decompress failed");
    }
    output.resize(stream.total_out);
    inflateEnd(&stream);
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
