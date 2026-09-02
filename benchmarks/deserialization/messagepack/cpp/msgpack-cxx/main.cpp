#include <iostream>
#include <sstream>
#include <vector>

#include <msgpack.hpp>
#include <nlohmann/json.hpp>

#include "bench/dataset.hpp"
#include "bench/paths.hpp"
#include "bench/timing.hpp"

namespace {

std::vector<std::uint8_t> serialize_msgpack(const benchkit::Dataset& data) {
    const nlohmann::json json = std::visit(
        [](const auto& value) {
            nlohmann::json out;
            to_json(out, value);
            return out;
        },
        data);
    std::stringstream buffer;
    msgpack::pack(buffer, json);
    const std::string packed = buffer.str();
    return std::vector<std::uint8_t>(packed.begin(), packed.end());
}


benchkit::Dataset decode_msgpack(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const msgpack::object_handle handle =
        msgpack::unpack(reinterpret_cast<const char*>(payload.data()), payload.size());
    nlohmann::json json;
    handle.get().convert(json);
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") return benchkit::parse_logs(json);
    if (domain == "profile") return benchkit::parse_profile(json);
    if (domain == "mesh") return benchkit::parse_mesh(json);
    if (domain == "catalog") return benchkit::parse_catalog(json);
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
    const benchkit::Dataset data = benchkit::load(spec);
    const std::vector<std::uint8_t> payload = serialize_msgpack(data);
    const double load_seconds = benchkit::now_seconds() - load_start;
    const auto result = benchkit::run_deserialize_with_setup(
        load_seconds, payload, [&](const std::vector<std::uint8_t>& bytes) {
            return decode_msgpack(spec, bytes);
        });
    benchkit::print_result(result);
    return 0;
}
