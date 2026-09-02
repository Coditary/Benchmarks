#include "serialize.hpp"

#include <flatbuffers/flatbuffers.h>

#include "generated/benchmark_generated.h"

namespace fb_bench {
namespace {

using namespace benchmark;

flatbuffers::Offset<LogMetadata> build_log_metadata(flatbuffers::FlatBufferBuilder& builder,
                                                    const benchkit::LogMetadata& metadata) {
    return CreateLogMetadataDirect(builder, metadata.status, metadata.duration_ms,
                                   metadata.bytes_sent, metadata.user_agent.c_str(),
                                   metadata.remote_addr.c_str());
}

flatbuffers::Offset<LogEntry> build_log_entry(flatbuffers::FlatBufferBuilder& builder,
                                              const benchkit::LogEntry& entry) {
    return CreateLogEntryDirect(builder, entry.timestamp.c_str(), entry.level.c_str(),
                                entry.message.c_str(), entry.request_id.c_str(),
                                build_log_metadata(builder, entry.metadata));
}

std::vector<std::uint8_t> serialize_logs(const benchkit::LogDataset& data) {
    flatbuffers::FlatBufferBuilder builder(1024);
    std::vector<flatbuffers::Offset<LogEntry>> entries;
    entries.reserve(data.entries.size());
    for (const auto& entry : data.entries) {
        entries.push_back(build_log_entry(builder, entry));
    }
    const auto root = CreateLogDatasetDirect(builder, data.version, data.domain.c_str(),
                                             data.tier.c_str(), &entries);
    builder.Finish(root);
    const std::uint8_t* buffer = builder.GetBufferPointer();
    return std::vector<std::uint8_t>(buffer, buffer + builder.GetSize());
}

std::vector<std::uint8_t> serialize_profile(const benchkit::ProfileDataset& data) {
    flatbuffers::FlatBufferBuilder builder(1024);
    std::vector<flatbuffers::Offset<Profile>> profiles;
    profiles.reserve(data.profiles.size());
    for (const auto& profile : data.profiles) {
        std::vector<flatbuffers::Offset<flatbuffers::String>> tags;
        tags.reserve(profile.tags.size());
        for (const auto& tag : profile.tags) {
            tags.push_back(builder.CreateString(tag));
        }
        const auto preferences = CreateProfilePreferencesDirect(
            builder, profile.preferences.locale.c_str(), profile.preferences.newsletter,
            profile.preferences.theme.c_str());
        const auto address = CreateProfileAddressDirect(
            builder, profile.address.city.c_str(), profile.address.postal_code.c_str(),
            profile.address.country.c_str());
        profiles.push_back(CreateProfileDirect(builder, profile.id.c_str(), profile.name.c_str(),
                                               profile.email.c_str(), profile.active, &tags,
                                               preferences, address));
    }
    const auto root = CreateProfileDatasetDirect(builder, data.version, data.domain.c_str(),
                                                 data.tier.c_str(), &profiles);
    builder.Finish(root);
    const std::uint8_t* buffer = builder.GetBufferPointer();
    return std::vector<std::uint8_t>(buffer, buffer + builder.GetSize());
}

std::vector<std::uint8_t> serialize_mesh(const benchkit::MeshDataset& data) {
    flatbuffers::FlatBufferBuilder builder(1024);
    std::vector<flatbuffers::Offset<Vertex>> vertices;
    vertices.reserve(data.vertices.size());
    for (const auto& vertex : data.vertices) {
        vertices.push_back(
            CreateVertex(builder, vertex.x, vertex.y, vertex.z, vertex.nx, vertex.ny, vertex.nz));
    }
    const auto root =
        CreateMeshDatasetDirect(builder, data.version, data.domain.c_str(), data.tier.c_str(),
                                data.name.c_str(), &vertices, &data.indices);
    builder.Finish(root);
    const std::uint8_t* buffer = builder.GetBufferPointer();
    return std::vector<std::uint8_t>(buffer, buffer + builder.GetSize());
}

std::vector<std::uint8_t> serialize_catalog(const benchkit::CatalogDataset& data) {
    flatbuffers::FlatBufferBuilder builder(1024);
    std::vector<flatbuffers::Offset<Product>> products;
    products.reserve(data.products.size());
    for (const auto& product : data.products) {
        std::vector<flatbuffers::Offset<flatbuffers::String>> tags;
        tags.reserve(product.tags.size());
        for (const auto& tag : product.tags) {
            tags.push_back(builder.CreateString(tag));
        }
        std::vector<flatbuffers::Offset<KeyValue>> attributes;
        attributes.reserve(product.attributes.size());
        for (const auto& [key, value] : product.attributes) {
            attributes.push_back(CreateKeyValueDirect(builder, key.c_str(), value.c_str()));
        }
        products.push_back(CreateProductDirect(builder, product.sku.c_str(), product.name.c_str(),
                                               product.price_cents, product.currency.c_str(),
                                               product.in_stock, &tags, &attributes));
    }
    const auto root = CreateCatalogDatasetDirect(builder, data.version, data.domain.c_str(),
                                                 data.tier.c_str(), &products);
    builder.Finish(root);
    const std::uint8_t* buffer = builder.GetBufferPointer();
    return std::vector<std::uint8_t>(buffer, buffer + builder.GetSize());
}

}  // namespace

std::vector<std::uint8_t> serialize(const benchkit::Dataset& data) {
    return std::visit(
        [](const auto& value) -> std::vector<std::uint8_t> {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, benchkit::LogDataset>) {
                return serialize_logs(value);
            } else if constexpr (std::is_same_v<T, benchkit::ProfileDataset>) {
                return serialize_profile(value);
            } else if constexpr (std::is_same_v<T, benchkit::MeshDataset>) {
                return serialize_mesh(value);
            } else if constexpr (std::is_same_v<T, benchkit::CatalogDataset>) {
                return serialize_catalog(value);
            } else {
                return {};
            }
        },
        data);
}

}  // namespace fb_bench
