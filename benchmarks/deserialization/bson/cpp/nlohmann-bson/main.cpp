#include <iostream>
#include <string>
#include <vector>

#include "bench/text/bson.hpp"
#include "bench/dataset.hpp"
#include "bench/paths.hpp"
#include "bench/timing.hpp"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const std::vector<std::uint8_t> payload = bson_bench::encode(data);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload,
        [spec](const std::vector<std::uint8_t>& bytes) -> benchkit::Dataset {
            return bson_bench::decode(spec, bytes);
        });
    benchkit::print_result(result);
    return 0;
}
