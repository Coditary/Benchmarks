#include "convert.hpp"

#include <google/protobuf/util/json_util.h>

namespace pb {

namespace {

::bench::LogDataset to_proto(const benchkit::LogDataset& data) {
    ::bench::LogDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    for (const auto& entry : data.entries) {
        auto* item = out.add_entries();
        item->set_timestamp(entry.timestamp);
        item->set_level(entry.level);
        item->set_message(entry.message);
        item->set_request_id(entry.request_id);
        auto* meta = item->mutable_metadata();
        meta->set_status(entry.metadata.status);
        meta->set_duration_ms(entry.metadata.duration_ms);
        meta->set_bytes_sent(entry.metadata.bytes_sent);
        meta->set_user_agent(entry.metadata.user_agent);
        meta->set_remote_addr(entry.metadata.remote_addr);
    }
    return out;
}

benchkit::LogDataset from_proto(const ::bench::LogDataset& data) {
    benchkit::LogDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.entries.reserve(static_cast<std::size_t>(data.entries_size()));
    for (const auto& entry : data.entries()) {
        benchkit::LogEntry item;
        item.timestamp = entry.timestamp();
        item.level = entry.level();
        item.message = entry.message();
        item.request_id = entry.request_id();
        item.metadata.status = static_cast<std::uint16_t>(entry.metadata().status());
        item.metadata.duration_ms = entry.metadata().duration_ms();
        item.metadata.bytes_sent = entry.metadata().bytes_sent();
        item.metadata.user_agent = entry.metadata().user_agent();
        item.metadata.remote_addr = entry.metadata().remote_addr();
        out.entries.push_back(std::move(item));
    }
    return out;
}

::::bench::ProfileDataset to_proto(const benchkit::ProfileDataset& data) {
    ::bench::ProfileDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    for (const auto& profile : data.profiles) {
        auto* item = out.add_profiles();
        item->set_id(profile.id);
        item->set_name(profile.name);
        item->set_email(profile.email);
        item->set_active(profile.active);
        for (const auto& tag : profile.tags) {
            item->add_tags(tag);
        }
        item->mutable_preferences()->set_locale(profile.preferences.locale);
        item->mutable_preferences()->set_newsletter(profile.preferences.newsletter);
        item->mutable_preferences()->set_theme(profile.preferences.theme);
        item->mutable_address()->set_city(profile.address.city);
        item->mutable_address()->set_postal_code(profile.address.postal_code);
        item->mutable_address()->set_country(profile.address.country);
    }
    return out;
}

benchkit::ProfileDataset from_proto(const ::bench::ProfileDataset& data) {
    benchkit::ProfileDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.profiles.reserve(static_cast<std::size_t>(data.profiles_size()));
    for (const auto& profile : data.profiles()) {
        benchkit::Profile item;
        item.id = profile.id();
        item.name = profile.name();
        item.email = profile.email();
        item.active = profile.active();
        item.tags.reserve(static_cast<std::size_t>(profile.tags_size()));
        for (const auto& tag : profile.tags()) {
            item.tags.push_back(tag);
        }
        item.preferences.locale = profile.preferences().locale();
        item.preferences.newsletter = profile.preferences().newsletter();
        item.preferences.theme = profile.preferences().theme();
        item.address.city = profile.address().city();
        item.address.postal_code = profile.address().postal_code();
        item.address.country = profile.address().country();
        out.profiles.push_back(std::move(item));
    }
    return out;
}

::::bench::MeshDataset to_proto(const benchkit::MeshDataset& data) {
    ::bench::MeshDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    out.set_name(data.name);
    for (const auto& vertex : data.vertices) {
        auto* item = out.add_vertices();
        item->set_x(vertex.x);
        item->set_y(vertex.y);
        item->set_z(vertex.z);
        item->set_nx(vertex.nx);
        item->set_ny(vertex.ny);
        item->set_nz(vertex.nz);
    }
    for (const auto index : data.indices) {
        out.add_indices(index);
    }
    return out;
}

benchkit::MeshDataset from_proto(const ::bench::MeshDataset& data) {
    benchkit::MeshDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.name = data.name();
    out.vertices.reserve(static_cast<std::size_t>(data.vertices_size()));
    for (const auto& vertex : data.vertices()) {
        out.vertices.push_back(
            benchkit::Vertex{vertex.x(), vertex.y(), vertex.z(), vertex.nx(), vertex.ny(), vertex.nz()});
    }
    out.indices.reserve(static_cast<std::size_t>(data.indices_size()));
    for (const auto index : data.indices()) {
        out.indices.push_back(index);
    }
    return out;
}

::::bench::CatalogDataset to_proto(const benchkit::CatalogDataset& data) {
    ::bench::CatalogDataset out;
    out.set_version(data.version);
    out.set_domain(data.domain);
    out.set_tier(data.tier);
    for (const auto& product : data.products) {
        auto* item = out.add_products();
        item->set_sku(product.sku);
        item->set_name(product.name);
        item->set_price_cents(product.price_cents);
        item->set_currency(product.currency);
        item->set_in_stock(product.in_stock);
        for (const auto& tag : product.tags) {
            item->add_tags(tag);
        }
        auto* attrs = item->mutable_attributes();
        for (const auto& [key, value] : product.attributes) {
            (*attrs)[key] = value;
        }
    }
    return out;
}

benchkit::CatalogDataset from_proto(const ::bench::CatalogDataset& data) {
    benchkit::CatalogDataset out;
    out.version = data.version();
    out.domain = data.domain();
    out.tier = data.tier();
    out.products.reserve(static_cast<std::size_t>(data.products_size()));
    for (const auto& product : data.products()) {
        benchkit::Product item;
        item.sku = product.sku();
        item.name = product.name();
        item.price_cents = product.price_cents();
        item.currency = product.currency();
        item.in_stock = product.in_stock();
        item.tags.reserve(static_cast<std::size_t>(product.tags_size()));
        for (const auto& tag : product.tags()) {
            item.tags.push_back(tag);
        }
        for (const auto& [key, value] : product.attributes()) {
            item.attributes.emplace(key, value);
        }
        out.products.push_back(std::move(item));
    }
    return out;
}

}  // namespace

Prepared prepare(const benchkit::Dataset& data) {
    Prepared prepared;
    std::visit(
        [&](const auto& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, benchkit::LogDataset>) {
                prepared.domain = "logs";
                prepared.logs = to_proto(value);
            } else if constexpr (std::is_same_v<T, benchkit::ProfileDataset>) {
                prepared.domain = "profile";
                prepared.profile = to_proto(value);
            } else if constexpr (std::is_same_v<T, benchkit::MeshDataset>) {
                prepared.domain = "mesh";
                prepared.mesh = to_proto(value);
            } else if constexpr (std::is_same_v<T, benchkit::CatalogDataset>) {
                prepared.domain = "catalog";
                prepared.catalog = to_proto(value);
            }
        },
        data);
    return prepared;
}

std::vector<std::uint8_t> encode(const Prepared& prepared) {
    std::string bytes;
    if (prepared.domain == "logs") {
        prepared.logs.SerializeToString(&bytes);
    } else if (prepared.domain == "profile") {
        prepared.profile.SerializeToString(&bytes);
    } else if (prepared.domain == "mesh") {
        prepared.mesh.SerializeToString(&bytes);
    } else if (prepared.domain == "catalog") {
        prepared.catalog.SerializeToString(&bytes);
    }
    return std::vector<std::uint8_t>(bytes.begin(), bytes.end());
}

benchkit::Dataset decode_materialized(const std::string& spec, const std::vector<std::uint8_t>& payload) {
    const std::string domain = benchkit::domain_from_spec(spec);
    if (domain == "logs") {
        ::bench::LogDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    if (domain == "profile") {
        ::bench::ProfileDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    if (domain == "mesh") {
        ::bench::MeshDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    if (domain == "catalog") {
        ::bench::CatalogDataset message;
        message.ParseFromArray(payload.data(), static_cast<int>(payload.size()));
        return from_proto(message);
    }
    throw std::runtime_error("unknown domain");
}

}  // namespace pb
