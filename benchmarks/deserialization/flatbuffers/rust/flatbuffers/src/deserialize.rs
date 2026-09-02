use std::collections::BTreeMap;

use bench_support::catalog::{CatalogDataset, Product};
use bench_support::deserialize::DecodedDataset;
use bench_support::logs::{LogDataset, LogEntry, LogMetadata};
use bench_support::mesh::{MeshDataset, Vertex};
use bench_support::profile::{
    Profile, ProfileAddress, ProfileDataset, ProfilePreferences,
};
use bench_support::shared::domain_from_spec;

mod benchmark_generated {
    include!(concat!(env!("OUT_DIR"), "/benchmark_generated.rs"));
}

use benchmark_generated::benchmark::{
    CatalogDataset as FbCatalogDataset, LogDataset as FbLogDataset, LogEntry as FbLogEntry,
    LogMetadata as FbLogMetadata, MeshDataset as FbMeshDataset, Product as FbProduct,
    Profile as FbProfile, ProfileAddress as FbProfileAddress, ProfileDataset as FbProfileDataset,
    ProfilePreferences as FbProfilePreferences,
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

fn read_string(value: Option<&str>) -> String {
    value.unwrap_or("").to_owned()
}

fn materialize_logs(bytes: &[u8]) -> LogDataset {
    let root = flatbuffers::root::<FbLogDataset>(bytes).expect("decode");
    let mut entries = Vec::new();
    if let Some(items) = root.entries() {
        entries.reserve(items.len());
        for index in 0..items.len() {
            entries.push(materialize_log_entry(items.get(index)));
        }
    }
    LogDataset {
        version: root.version(),
        domain: read_string(root.domain()),
        tier: read_string(root.tier()),
        entries,
    }
}

fn materialize_log_entry(entry: FbLogEntry<'_>) -> LogEntry {
    let metadata = entry.metadata().expect("metadata");
    LogEntry {
        timestamp: read_string(entry.timestamp()),
        level: read_string(entry.level()),
        message: read_string(entry.message()),
        request_id: read_string(entry.request_id()),
        metadata: materialize_log_metadata(metadata),
    }
}

fn materialize_log_metadata(metadata: FbLogMetadata<'_>) -> LogMetadata {
    LogMetadata {
        status: metadata.status(),
        duration_ms: metadata.duration_ms(),
        bytes_sent: metadata.bytes_sent(),
        user_agent: read_string(metadata.user_agent()),
        remote_addr: read_string(metadata.remote_addr()),
    }
}

fn materialize_profile(bytes: &[u8]) -> ProfileDataset {
    let root = flatbuffers::root::<FbProfileDataset>(bytes).expect("decode");
    let mut profiles = Vec::new();
    if let Some(items) = root.profiles() {
        profiles.reserve(items.len());
        for index in 0..items.len() {
            profiles.push(materialize_profile_entry(items.get(index)));
        }
    }
    ProfileDataset {
        version: root.version(),
        domain: read_string(root.domain()),
        tier: read_string(root.tier()),
        profiles,
    }
}

fn materialize_profile_entry(profile: FbProfile<'_>) -> Profile {
    let preferences = profile.preferences().expect("preferences");
    let address = profile.address().expect("address");
    let mut tags = Vec::new();
    if let Some(items) = profile.tags() {
        tags.reserve(items.len());
        for index in 0..items.len() {
            tags.push(read_string(Some(items.get(index))));
        }
    }
    Profile {
        id: read_string(profile.id()),
        name: read_string(profile.name()),
        email: read_string(profile.email()),
        active: profile.active(),
        tags,
        preferences: ProfilePreferences {
            locale: read_string(preferences.locale()),
            newsletter: preferences.newsletter(),
            theme: read_string(preferences.theme()),
        },
        address: ProfileAddress {
            city: read_string(address.city()),
            postal_code: read_string(address.postal_code()),
            country: read_string(address.country()),
        },
    }
}

fn materialize_mesh(bytes: &[u8]) -> MeshDataset {
    let root = flatbuffers::root::<FbMeshDataset>(bytes).expect("decode");
    let mut vertices = Vec::new();
    if let Some(items) = root.vertices() {
        vertices.reserve(items.len());
        for index in 0..items.len() {
            let vertex = items.get(index);
            vertices.push(Vertex {
                x: vertex.x(),
                y: vertex.y(),
                z: vertex.z(),
                nx: vertex.nx(),
                ny: vertex.ny(),
                nz: vertex.nz(),
            });
        }
    }
    let mut indices = Vec::new();
    if let Some(items) = root.indices() {
        indices.reserve(items.len());
        for index in 0..items.len() {
            indices.push(items.get(index));
        }
    }
    MeshDataset {
        version: root.version(),
        domain: read_string(root.domain()),
        tier: read_string(root.tier()),
        name: read_string(root.name()),
        vertices,
        indices,
    }
}

fn materialize_catalog(bytes: &[u8]) -> CatalogDataset {
    let root = flatbuffers::root::<FbCatalogDataset>(bytes).expect("decode");
    let mut products = Vec::new();
    if let Some(items) = root.products() {
        products.reserve(items.len());
        for index in 0..items.len() {
            products.push(materialize_product(items.get(index)));
        }
    }
    CatalogDataset {
        version: root.version(),
        domain: read_string(root.domain()),
        tier: read_string(root.tier()),
        products,
    }
}

fn materialize_product(product: FbProduct<'_>) -> Product {
    let mut tags = Vec::new();
    if let Some(items) = product.tags() {
        tags.reserve(items.len());
        for index in 0..items.len() {
            tags.push(read_string(Some(items.get(index))));
        }
    }
    let mut attributes = BTreeMap::new();
    if let Some(items) = product.attributes() {
        for index in 0..items.len() {
            let attribute = items.get(index);
            attributes.insert(
                read_string(attribute.key()),
                read_string(attribute.value()),
            );
        }
    }
    Product {
        sku: read_string(product.sku()),
        name: read_string(product.name()),
        price_cents: product.price_cents(),
        currency: read_string(product.currency()),
        in_stock: product.in_stock(),
        tags,
        attributes,
    }
}
