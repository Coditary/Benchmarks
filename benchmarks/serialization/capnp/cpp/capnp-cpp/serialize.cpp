#include "serialize.hpp"

#include <capnp/message.h>
#include <capnp/serialize.h>
#include <kj/io.h>

#include "benchmark.capnp.h"

namespace capnp_bench {
namespace {

using LogMetadataBuilder = LogMetadata::Builder;
using LogEntryBuilder = LogEntry::Builder;

std::vector<std::uint8_t> write_message(capnp::MallocMessageBuilder& message) {
    kj::VectorOutputStream stream;
    capnp::writeMessage(stream, message);
    const auto array = stream.getArray();
    return std::vector<std::uint8_t>(array.begin(), array.end());
}

void populate_log_metadata(LogMetadataBuilder builder, const benchkit::LogMetadata& metadata) {
    builder.setStatus(metadata.status);
    builder.setDurationMs(metadata.duration_ms);
    builder.setBytesSent(metadata.bytes_sent);
    builder.setUserAgent(metadata.user_agent);
    builder.setRemoteAddr(metadata.remote_addr);
}

void populate_log_entry(LogEntryBuilder builder, const benchkit::LogEntry& entry) {
    builder.setTimestamp(entry.timestamp);
    builder.setLevel(entry.level);
    builder.setMessage(entry.message);
    builder.setRequestId(entry.request_id);
    populate_log_metadata(builder.initMetadata(), entry.metadata);
}

std::vector<std::uint8_t> serialize_logs(const benchkit::LogDataset& data) {
    capnp::MallocMessageBuilder message;
    auto root = message.initRoot<LogDataset>();
    root.setVersion(data.version);
    root.setDomain(data.domain);
    root.setTier(data.tier);
    auto entries = root.initEntries(static_cast<unsigned int>(data.entries.size()));
    for (std::size_t index = 0; index < data.entries.size(); ++index) {
        populate_log_entry(entries[static_cast<unsigned int>(index)], data.entries[index]);
    }
    return write_message(message);
}

void populate_profile(Profile::Builder builder, const benchkit::Profile& profile) {
    builder.setId(profile.id);
    builder.setName(profile.name);
    builder.setEmail(profile.email);
    builder.setActive(profile.active);
    auto tags = builder.initTags(static_cast<unsigned int>(profile.tags.size()));
    for (std::size_t index = 0; index < profile.tags.size(); ++index) {
        tags.set(static_cast<unsigned int>(index), profile.tags[index]);
    }
    auto preferences = builder.initPreferences();
    preferences.setLocale(profile.preferences.locale);
    preferences.setNewsletter(profile.preferences.newsletter);
    preferences.setTheme(profile.preferences.theme);
    auto address = builder.initAddress();
    address.setCity(profile.address.city);
    address.setPostalCode(profile.address.postal_code);
    address.setCountry(profile.address.country);
}

std::vector<std::uint8_t> serialize_profile(const benchkit::ProfileDataset& data) {
    capnp::MallocMessageBuilder message;
    auto root = message.initRoot<ProfileDataset>();
    root.setVersion(data.version);
    root.setDomain(data.domain);
    root.setTier(data.tier);
    auto profiles = root.initProfiles(static_cast<unsigned int>(data.profiles.size()));
    for (std::size_t index = 0; index < data.profiles.size(); ++index) {
        populate_profile(profiles[static_cast<unsigned int>(index)], data.profiles[index]);
    }
    return write_message(message);
}

std::vector<std::uint8_t> serialize_mesh(const benchkit::MeshDataset& data) {
    capnp::MallocMessageBuilder message;
    auto root = message.initRoot<MeshDataset>();
    root.setVersion(data.version);
    root.setDomain(data.domain);
    root.setTier(data.tier);
    root.setName(data.name);
    auto vertices = root.initVertices(static_cast<unsigned int>(data.vertices.size()));
    for (std::size_t index = 0; index < data.vertices.size(); ++index) {
        const auto& vertex = data.vertices[index];
        auto item = vertices[static_cast<unsigned int>(index)];
        item.setX(vertex.x);
        item.setY(vertex.y);
        item.setZ(vertex.z);
        item.setNx(vertex.nx);
        item.setNy(vertex.ny);
        item.setNz(vertex.nz);
    }
    auto indices = root.initIndices(static_cast<unsigned int>(data.indices.size()));
    for (std::size_t index = 0; index < data.indices.size(); ++index) {
        indices.set(static_cast<unsigned int>(index), data.indices[index]);
    }
    return write_message(message);
}

void populate_product(Product::Builder builder, const benchkit::Product& product) {
    builder.setSku(product.sku);
    builder.setName(product.name);
    builder.setPriceCents(product.price_cents);
    builder.setCurrency(product.currency);
    builder.setInStock(product.in_stock);
    auto tags = builder.initTags(static_cast<unsigned int>(product.tags.size()));
    for (std::size_t index = 0; index < product.tags.size(); ++index) {
        tags.set(static_cast<unsigned int>(index), product.tags[index]);
    }
    auto attributes = builder.initAttributes(static_cast<unsigned int>(product.attributes.size()));
    std::size_t attr_index = 0;
    for (const auto& [key, value] : product.attributes) {
        auto item = attributes[static_cast<unsigned int>(attr_index++)];
        item.setKey(key);
        item.setValue(value);
    }
}

std::vector<std::uint8_t> serialize_catalog(const benchkit::CatalogDataset& data) {
    capnp::MallocMessageBuilder message;
    auto root = message.initRoot<CatalogDataset>();
    root.setVersion(data.version);
    root.setDomain(data.domain);
    root.setTier(data.tier);
    auto products = root.initProducts(static_cast<unsigned int>(data.products.size()));
    for (std::size_t index = 0; index < data.products.size(); ++index) {
        populate_product(products[static_cast<unsigned int>(index)], data.products[index]);
    }
    return write_message(message);
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

}  // namespace capnp_bench
