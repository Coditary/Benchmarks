#include <iostream>
#include <string>

#include "bench/dataset.hpp"
#include "bench/timing.hpp"
#include "convert.hpp"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const pb::Prepared prepared = pb::prepare(data);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_with_setup(load_seconds, prepared, pb::encode);
    benchkit::print_result(result);
    return 0;
}
