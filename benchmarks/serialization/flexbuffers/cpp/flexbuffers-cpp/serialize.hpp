#pragma once

#include <cstdint>
#include <vector>

#include "bench/dataset.hpp"

namespace flex_bench {

std::vector<std::uint8_t> serialize(const benchkit::Dataset& data);

}  // namespace flex_bench
