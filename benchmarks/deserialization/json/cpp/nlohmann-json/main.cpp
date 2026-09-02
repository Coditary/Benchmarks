#include <iostream>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "bench/dataset.hpp"
#include "bench/paths.hpp"
#include "bench/timing.hpp"

namespace {

benchkit::Dataset decode_json(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const nlohmann::json json =
        nlohmann::json::parse(payload.begin(), payload.end());
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") {
        return benchkit::parse_logs(json);
    }
    if (domain == "profile") {
        return benchkit::parse_profile(json);
    }
    if (domain == "mesh") {
        return benchkit::parse_mesh(json);
    }
    if (domain == "catalog") {
        return benchkit::parse_catalog(json);
    }
    throw std::runtime_error("unknown domain");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: bench <domain>/<tier>\n";
        return 1;
    }
    const std::string spec = argv[1];
    const double load_start = benchkit::now_seconds();
    const std::vector<std::uint8_t> payload = benchkit::load_canonical_bytes(spec);
    const double load_seconds = benchkit::now_seconds() - load_start;

    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload,
        [spec](const std::vector<std::uint8_t>& bytes) -> benchkit::Dataset {
            return decode_json(spec, bytes);
        });
    benchkit::print_result(result);
    return 0;
}
