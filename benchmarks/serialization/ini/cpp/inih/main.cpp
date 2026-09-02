#include <iostream>
#include <string>
#include <vector>

#include "bench/text/ini.hpp"
#include "bench/dataset.hpp"
#include "bench/timing.hpp"

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const benchkit::Dataset data = benchkit::load(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_with_setup(load_seconds, data, ini_bench::encode);
    benchkit::print_result(result);
    return 0;
}
