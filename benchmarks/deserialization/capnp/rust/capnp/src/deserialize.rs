use std::collections::BTreeMap;

use bench_support::catalog::{CatalogDataset, Product};
use bench_support::deserialize::DecodedDataset;
use bench_support::logs::{LogDataset, LogEntry, LogMetadata};
use bench_support::mesh::{MeshDataset, Vertex};
use bench_support::profile::{
    Profile, ProfileAddress, ProfileDataset, ProfilePreferences,
};
use bench_support::shared::domain_from_spec;

use crate::benchmark_capnp::{
    catalog_dataset, log_dataset, log_entry, log_metadata, mesh_dataset, product,
    profile as capnp_profile, profile_dataset,
};

pub fn decode(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(materialize_logs(bytes)),
        "profile" => DecodedDataset::Profile(materialize_profile(bytes)),
        "mesh" => DecodedDataset::Mesh(materialize_mesh(bytes)),
        "catalog" => DecodedDataset::Catalog(materialize_catalog(bytes)),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn read_message(bytes: &[u8]) -> capnp::message::Reader<capnp::serialize::OwnedSegments> {
    capnp::serialize::read_message(
        &mut &bytes[..],
        capnp::message::ReaderOptions::new(),
    )
    .expect("decode")
}

fn read_text(value: capnp::text::Reader<'_>) -> String {
    value.to_str().expect("utf8").to_owned()
}

fn materialize_logs(bytes: &[u8]) -> LogDataset {
    let message = read_message(bytes);
    let root = message
        .get_root::<log_dataset::Reader>()
        .expect("root");
    let entries_reader = root.get_entries().expect("entries");
    let mut entries = Vec::with_capacity(entries_reader.len() as usize);
    for entry in entries_reader {
        entries.push(materialize_log_entry(entry));
    }
    LogDataset {
        version: root.get_version(),
        domain: read_text(root.get_domain().expect("domain")),
        tier: read_text(root.get_tier().expect("tier")),
        entries,
    }
}

fn materialize_log_entry(entry: log_entry::Reader<'_>) -> LogEntry {
    let metadata = entry.get_metadata().expect("metadata");
    LogEntry {
        timestamp: read_text(entry.get_timestamp().expect("timestamp")),
        level: read_text(entry.get_level().expect("level")),
        message: read_text(entry.get_message().expect("message")),
        request_id: read_text(entry.get_request_id().expect("request_id")),
        metadata: materialize_log_metadata(metadata),
    }
}

fn materialize_log_metadata(metadata: log_metadata::Reader<'_>) -> LogMetadata {
    LogMetadata {
        status: metadata.get_status(),
        duration_ms: metadata.get_duration_ms(),
        bytes_sent: metadata.get_bytes_sent(),
        user_agent: read_text(metadata.get_user_agent().expect("user_agent")),
        remote_addr: read_text(metadata.get_remote_addr().expect("remote_addr")),
    }
}

fn materialize_profile(bytes: &[u8]) -> ProfileDataset {
    let message = read_message(bytes);
    let root = message
        .get_root::<profile_dataset::Reader>()
        .expect("root");
    let profiles_reader = root.get_profiles().expect("profiles");
    let mut profiles = Vec::with_capacity(profiles_reader.len() as usize);
    for profile in profiles_reader {
        profiles.push(materialize_profile_entry(profile));
    }
    ProfileDataset {
        version: root.get_version(),
        domain: read_text(root.get_domain().expect("domain")),
        tier: read_text(root.get_tier().expect("tier")),
        profiles,
    }
}

fn materialize_profile_entry(profile: capnp_profile::Reader<'_>) -> Profile {
    let preferences = profile.get_preferences().expect("preferences");
    let address = profile.get_address().expect("address");
    let tags_reader = profile.get_tags().expect("tags");
    let mut tags = Vec::with_capacity(tags_reader.len() as usize);
    for tag in tags_reader {
        tags.push(read_text(tag.expect("tag")));
    }
    Profile {
        id: read_text(profile.get_id().expect("id")),
        name: read_text(profile.get_name().expect("name")),
        email: read_text(profile.get_email().expect("email")),
        active: profile.get_active(),
        tags,
        preferences: ProfilePreferences {
            locale: read_text(preferences.get_locale().expect("locale")),
            newsletter: preferences.get_newsletter(),
            theme: read_text(preferences.get_theme().expect("theme")),
        },
        address: ProfileAddress {
            city: read_text(address.get_city().expect("city")),
            postal_code: read_text(address.get_postal_code().expect("postal_code")),
            country: read_text(address.get_country().expect("country")),
        },
    }
}

fn materialize_mesh(bytes: &[u8]) -> MeshDataset {
    let message = read_message(bytes);
    let root = message
        .get_root::<mesh_dataset::Reader>()
        .expect("root");
    let vertices_reader = root.get_vertices().expect("vertices");
    let mut vertices = Vec::with_capacity(vertices_reader.len() as usize);
    for vertex in vertices_reader {
        vertices.push(Vertex {
            x: vertex.get_x(),
            y: vertex.get_y(),
            z: vertex.get_z(),
            nx: vertex.get_nx(),
            ny: vertex.get_ny(),
            nz: vertex.get_nz(),
        });
    }
    let indices_reader = root.get_indices().expect("indices");
    let mut indices = Vec::with_capacity(indices_reader.len() as usize);
    for index in indices_reader {
        indices.push(index);
    }
    MeshDataset {
        version: root.get_version(),
        domain: read_text(root.get_domain().expect("domain")),
        tier: read_text(root.get_tier().expect("tier")),
        name: read_text(root.get_name().expect("name")),
        vertices,
        indices,
    }
}

fn materialize_catalog(bytes: &[u8]) -> CatalogDataset {
    let message = read_message(bytes);
    let root = message
        .get_root::<catalog_dataset::Reader>()
        .expect("root");
    let products_reader = root.get_products().expect("products");
    let mut products = Vec::with_capacity(products_reader.len() as usize);
    for item in products_reader {
        products.push(materialize_product(item));
    }
    CatalogDataset {
        version: root.get_version(),
        domain: read_text(root.get_domain().expect("domain")),
        tier: read_text(root.get_tier().expect("tier")),
        products,
    }
}

fn materialize_product(product: product::Reader<'_>) -> Product {
    let tags_reader = product.get_tags().expect("tags");
    let mut tags = Vec::with_capacity(tags_reader.len() as usize);
    for tag in tags_reader {
        tags.push(read_text(tag.expect("tag")));
    }
    let attributes_reader = product.get_attributes().expect("attributes");
    let mut attributes = BTreeMap::new();
    for attribute in attributes_reader {
        attributes.insert(
            read_text(attribute.get_key().expect("key")),
            read_text(attribute.get_value().expect("value")),
        );
    }
    Product {
        sku: read_text(product.get_sku().expect("sku")),
        name: read_text(product.get_name().expect("name")),
        price_cents: product.get_price_cents(),
        currency: read_text(product.get_currency().expect("currency")),
        in_stock: product.get_in_stock(),
        tags,
        attributes,
    }
}
