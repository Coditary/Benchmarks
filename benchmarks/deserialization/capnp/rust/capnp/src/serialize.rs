use bench_support::catalog::CatalogDataset;
use bench_support::dataset::Dataset;
use bench_support::logs::{LogDataset, LogEntry, LogMetadata};
use bench_support::mesh::MeshDataset;
use bench_support::profile::ProfileDataset;

use crate::benchmark_capnp::{
    catalog_dataset, log_dataset, log_entry, log_metadata, mesh_dataset, product, profile,
    profile_dataset,
};

pub fn serialize(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => serialize_logs(value),
        Dataset::Profile(value) => serialize_profile(value),
        Dataset::Mesh(value) => serialize_mesh(value),
        Dataset::Catalog(value) => serialize_catalog(value),
    }
}

fn serialize_logs(data: &LogDataset) -> Vec<u8> {
    let mut message = ::capnp::message::Builder::new_default();
    {
        let mut root = message.init_root::<log_dataset::Builder>();
        root.set_version(data.version);
        root.set_domain(&data.domain);
        root.set_tier(&data.tier);
        let mut entries = root.reborrow().init_entries(data.entries.len() as u32);
        for (index, entry) in data.entries.iter().enumerate() {
            populate_log_entry(&mut entries.reborrow().get(index as u32), entry);
        }
    }
    write_message(message)
}

fn serialize_profile(data: &ProfileDataset) -> Vec<u8> {
    let mut message = ::capnp::message::Builder::new_default();
    {
        let mut root = message.init_root::<profile_dataset::Builder>();
        root.set_version(data.version);
        root.set_domain(&data.domain);
        root.set_tier(&data.tier);
        let mut profiles = root.reborrow().init_profiles(data.profiles.len() as u32);
        for (index, profile) in data.profiles.iter().enumerate() {
            populate_profile(&mut profiles.reborrow().get(index as u32), profile);
        }
    }
    write_message(message)
}

fn serialize_mesh(data: &MeshDataset) -> Vec<u8> {
    let mut message = ::capnp::message::Builder::new_default();
    {
        let mut root = message.init_root::<mesh_dataset::Builder>();
        root.set_version(data.version);
        root.set_domain(&data.domain);
        root.set_tier(&data.tier);
        root.set_name(&data.name);
        let mut vertices = root.reborrow().init_vertices(data.vertices.len() as u32);
        for (index, vertex) in data.vertices.iter().enumerate() {
            let mut item = vertices.reborrow().get(index as u32);
            item.set_x(vertex.x);
            item.set_y(vertex.y);
            item.set_z(vertex.z);
            item.set_nx(vertex.nx);
            item.set_ny(vertex.ny);
            item.set_nz(vertex.nz);
        }
        let mut indices = root.reborrow().init_indices(data.indices.len() as u32);
        for (index, value) in data.indices.iter().enumerate() {
            indices.set(index as u32, *value);
        }
    }
    write_message(message)
}

fn serialize_catalog(data: &CatalogDataset) -> Vec<u8> {
    let mut message = ::capnp::message::Builder::new_default();
    {
        let mut root = message.init_root::<catalog_dataset::Builder>();
        root.set_version(data.version);
        root.set_domain(&data.domain);
        root.set_tier(&data.tier);
        let mut products = root.reborrow().init_products(data.products.len() as u32);
        for (index, product) in data.products.iter().enumerate() {
            populate_product(&mut products.reborrow().get(index as u32), product);
        }
    }
    write_message(message)
}

fn write_message(message: ::capnp::message::Builder<::capnp::message::HeapAllocator>) -> Vec<u8> {
    let mut buffer = Vec::new();
    capnp::serialize::write_message(&mut buffer, &message).expect("serialize output");
    buffer
}

fn populate_log_entry(builder: &mut log_entry::Builder, entry: &LogEntry) {
    builder.set_timestamp(&entry.timestamp);
    builder.set_level(&entry.level);
    builder.set_message(&entry.message);
    builder.set_request_id(&entry.request_id);
    populate_log_metadata(&mut builder.reborrow().init_metadata(), &entry.metadata);
}

fn populate_log_metadata(builder: &mut log_metadata::Builder, metadata: &LogMetadata) {
    builder.set_status(metadata.status);
    builder.set_duration_ms(metadata.duration_ms);
    builder.set_bytes_sent(metadata.bytes_sent);
    builder.set_user_agent(&metadata.user_agent);
    builder.set_remote_addr(&metadata.remote_addr);
}

fn populate_profile(builder: &mut profile::Builder, profile: &bench_support::profile::Profile) {
    builder.set_id(&profile.id);
    builder.set_name(&profile.name);
    builder.set_email(&profile.email);
    builder.set_active(profile.active);
    let mut tags = builder
        .reborrow()
        .init_tags(profile.tags.len() as u32);
    for (index, tag) in profile.tags.iter().enumerate() {
        tags.set(index as u32, tag);
    }
    let mut preferences = builder.reborrow().init_preferences();
    preferences.set_locale(&profile.preferences.locale);
    preferences.set_newsletter(profile.preferences.newsletter);
    preferences.set_theme(&profile.preferences.theme);
    let mut address = builder.reborrow().init_address();
    address.set_city(&profile.address.city);
    address.set_postal_code(&profile.address.postal_code);
    address.set_country(&profile.address.country);
}

fn populate_product(builder: &mut product::Builder, product: &bench_support::catalog::Product) {
    builder.set_sku(&product.sku);
    builder.set_name(&product.name);
    builder.set_price_cents(product.price_cents);
    builder.set_currency(&product.currency);
    builder.set_in_stock(product.in_stock);
    let mut tags = builder.reborrow().init_tags(product.tags.len() as u32);
    for (index, tag) in product.tags.iter().enumerate() {
        tags.set(index as u32, tag);
    }
    let mut attributes = builder
        .reborrow()
        .init_attributes(product.attributes.len() as u32);
    for (index, (key, value)) in product.attributes.iter().enumerate() {
        let mut item = attributes.reborrow().get(index as u32);
        item.set_key(key);
        item.set_value(value);
    }
}
