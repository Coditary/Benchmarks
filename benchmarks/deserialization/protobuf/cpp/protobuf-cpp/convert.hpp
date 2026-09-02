#pragma once

#include <string>
#include <vector>

#include "bench/dataset.hpp"
#include "benchmark.pb.h"

namespace pb {

benchkit::Dataset decode_materialized(const std::string& spec, const std::vector<std::uint8_t>& payload);

struct Prepared {
    ::bench::LogDataset logs;
    ::bench::ProfileDataset profile;
    ::bench::MeshDataset mesh;
    ::bench::CatalogDataset catalog;
    std::string domain;
};

Prepared prepare(const benchkit::Dataset& data);
std::vector<std::uint8_t> encode(const Prepared& prepared);

}  // namespace pb
