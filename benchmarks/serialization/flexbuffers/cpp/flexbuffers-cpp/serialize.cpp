#include "serialize.hpp"

#include <flatbuffers/flexbuffers.h>

namespace flex_bench {
namespace {

void write_log_metadata(flexbuffers::Builder& builder, const benchkit::LogMetadata& metadata) {
    builder.Key("status");
    builder.UInt(metadata.status);
    builder.Key("duration_ms");
    builder.UInt(metadata.duration_ms);
    builder.Key("bytes_sent");
    builder.UInt(metadata.bytes_sent);
    builder.Key("user_agent");
    builder.String(metadata.user_agent);
    builder.Key("remote_addr");
    builder.String(metadata.remote_addr);
}

void write_log_entry(flexbuffers::Builder& builder, const benchkit::LogEntry& entry) {
    const auto map = builder.StartMap();
    builder.Key("timestamp");
    builder.String(entry.timestamp);
    builder.Key("level");
    builder.String(entry.level);
    builder.Key("message");
    builder.String(entry.message);
    builder.Key("request_id");
    builder.String(entry.request_id);
    builder.Key("metadata");
    const auto metadata_map = builder.StartMap();
    write_log_metadata(builder, entry.metadata);
    builder.EndMap(metadata_map);
    builder.EndMap(map);
}

std::vector<std::uint8_t> serialize_logs(const benchkit::LogDataset& data) {
    flexbuffers::Builder builder(1024);
    const auto root = builder.StartMap();
    builder.Key("version");
    builder.UInt(data.version);
    builder.Key("domain");
    builder.String(data.domain);
    builder.Key("tier");
    builder.String(data.tier);
    builder.Key("entries");
    const auto entries = builder.StartVector();
    for (const auto& entry : data.entries) {
        write_log_entry(builder, entry);
    }
    builder.EndVector(entries, false, false);
    builder.EndMap(root);
  builder.Finish();
    const auto& buffer = builder.GetBuffer();
    return std::vector<std::uint8_t>(buffer.data(), buffer.data() + buffer.size());
}

void write_profile(flexbuffers::Builder& builder, const benchkit::Profile& profile) {
    const auto map = builder.StartMap();
    builder.Key("id");
    builder.String(profile.id);
    builder.Key("name");
    builder.String(profile.name);
    builder.Key("email");
    builder.String(profile.email);
    builder.Key("active");
    builder.Bool(profile.active);
    builder.Key("tags");
    const auto tags = builder.StartVector();
    for (const auto& tag : profile.tags) {
        builder.String(tag);
    }
    builder.EndVector(tags, false, false);
    builder.Key("preferences");
    const auto preferences = builder.StartMap();
    builder.Key("locale");
    builder.String(profile.preferences.locale);
    builder.Key("newsletter");
    builder.Bool(profile.preferences.newsletter);
    builder.Key("theme");
    builder.String(profile.preferences.theme);
    builder.EndMap(preferences);
    builder.Key("address");
    const auto address = builder.StartMap();
    builder.Key("city");
    builder.String(profile.address.city);
    builder.Key("postal_code");
    builder.String(profile.address.postal_code);
    builder.Key("country");
    builder.String(profile.address.country);
    builder.EndMap(address);
    builder.EndMap(map);
}

std::vector<std::uint8_t> serialize_profile(const benchkit::ProfileDataset& data) {
    flexbuffers::Builder builder(1024);
    const auto root = builder.StartMap();
    builder.Key("version");
    builder.UInt(data.version);
    builder.Key("domain");
    builder.String(data.domain);
    builder.Key("tier");
    builder.String(data.tier);
    builder.Key("profiles");
    const auto profiles = builder.StartVector();
    for (const auto& profile : data.profiles) {
        write_profile(builder, profile);
    }
    builder.EndVector(profiles, false, false);
    builder.EndMap(root);
    builder.Finish();
    const auto& buffer = builder.GetBuffer();
    return std::vector<std::uint8_t>(buffer.data(), buffer.data() + buffer.size());
}

std::vector<std::uint8_t> serialize_mesh(const benchkit::MeshDataset& data) {
    flexbuffers::Builder builder(1024);
    const auto root = builder.StartMap();
    builder.Key("version");
    builder.UInt(data.version);
    builder.Key("domain");
    builder.String(data.domain);
    builder.Key("tier");
    builder.String(data.tier);
    builder.Key("name");
    builder.String(data.name);
    builder.Key("vertices");
    const auto vertices = builder.StartVector();
    for (const auto& vertex : data.vertices) {
        const auto map = builder.StartMap();
        builder.Key("x");
        builder.Float(vertex.x);
        builder.Key("y");
        builder.Float(vertex.y);
        builder.Key("z");
        builder.Float(vertex.z);
        builder.Key("nx");
        builder.Float(vertex.nx);
        builder.Key("ny");
        builder.Float(vertex.ny);
        builder.Key("nz");
        builder.Float(vertex.nz);
        builder.EndMap(map);
    }
    builder.EndVector(vertices, false, false);
    builder.Key("indices");
    const auto indices = builder.StartVector();
    for (const auto index : data.indices) {
        builder.UInt(index);
    }
    builder.EndVector(indices, false, false);
    builder.EndMap(root);
    builder.Finish();
    const auto& buffer = builder.GetBuffer();
    return std::vector<std::uint8_t>(buffer.data(), buffer.data() + buffer.size());
}

void write_product(flexbuffers::Builder& builder, const benchkit::Product& product) {
    const auto map = builder.StartMap();
    builder.Key("sku");
    builder.String(product.sku);
    builder.Key("name");
    builder.String(product.name);
    builder.Key("price_cents");
    builder.UInt(product.price_cents);
    builder.Key("currency");
    builder.String(product.currency);
    builder.Key("in_stock");
    builder.Bool(product.in_stock);
    builder.Key("tags");
    const auto tags = builder.StartVector();
    for (const auto& tag : product.tags) {
        builder.String(tag);
    }
    builder.EndVector(tags, false, false);
    builder.Key("attributes");
    const auto attributes = builder.StartMap();
    for (const auto& [key, value] : product.attributes) {
        builder.Key(key);
        builder.String(value);
    }
    builder.EndMap(attributes);
    builder.EndMap(map);
}

std::vector<std::uint8_t> serialize_catalog(const benchkit::CatalogDataset& data) {
    flexbuffers::Builder builder(1024);
    const auto root = builder.StartMap();
    builder.Key("version");
    builder.UInt(data.version);
    builder.Key("domain");
    builder.String(data.domain);
    builder.Key("tier");
    builder.String(data.tier);
    builder.Key("products");
    const auto products = builder.StartVector();
    for (const auto& product : data.products) {
        write_product(builder, product);
    }
    builder.EndVector(products, false, false);
    builder.EndMap(root);
    builder.Finish();
    const auto& buffer = builder.GetBuffer();
    return std::vector<std::uint8_t>(buffer.data(), buffer.data() + buffer.size());
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

}  // namespace flex_bench
