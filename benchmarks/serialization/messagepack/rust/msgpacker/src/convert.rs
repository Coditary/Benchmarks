use std::collections::BTreeMap;

use bench_support::dataset::Dataset;
use msgpacker::{MsgPacker, Packable};

#[derive(MsgPacker)]
struct MpackLogMetadata {
    status: u16,
    duration_ms: u32,
    bytes_sent: u32,
    user_agent: String,
    remote_addr: String,
}

#[derive(MsgPacker)]
struct MpackLogEntry {
    timestamp: String,
    level: String,
    message: String,
    request_id: String,
    metadata: MpackLogMetadata,
}

#[derive(MsgPacker)]
struct MpackLogDataset {
    version: u32,
    domain: String,
    tier: String,
    entries: Vec<MpackLogEntry>,
}

#[derive(MsgPacker)]
struct MpackProfilePreferences {
    locale: String,
    newsletter: bool,
    theme: String,
}

#[derive(MsgPacker)]
struct MpackProfileAddress {
    city: String,
    postal_code: String,
    country: String,
}

#[derive(MsgPacker)]
struct MpackProfile {
    id: String,
    name: String,
    email: String,
    active: bool,
    tags: Vec<String>,
    preferences: MpackProfilePreferences,
    address: MpackProfileAddress,
}

#[derive(MsgPacker)]
struct MpackProfileDataset {
    version: u32,
    domain: String,
    tier: String,
    profiles: Vec<MpackProfile>,
}

#[derive(MsgPacker)]
struct MpackVertex {
    x: f32,
    y: f32,
    z: f32,
    nx: f32,
    ny: f32,
    nz: f32,
}

#[derive(MsgPacker)]
struct MpackMeshDataset {
    version: u32,
    domain: String,
    tier: String,
    name: String,
    vertices: Vec<MpackVertex>,
    indices: Vec<u32>,
}

#[derive(MsgPacker)]
struct MpackProduct {
    sku: String,
    name: String,
    price_cents: u32,
    currency: String,
    in_stock: bool,
    tags: Vec<String>,
    attributes: BTreeMap<String, String>,
}

#[derive(MsgPacker)]
struct MpackCatalogDataset {
    version: u32,
    domain: String,
    tier: String,
    products: Vec<MpackProduct>,
}

pub enum PreparedMpack {
    Logs(MpackLogDataset),
    Profile(MpackProfileDataset),
    Mesh(MpackMeshDataset),
    Catalog(MpackCatalogDataset),
}

pub fn prepare(data: Dataset) -> PreparedMpack {
    match data {
        Dataset::Logs(value) => PreparedMpack::Logs(MpackLogDataset {
            version: value.version,
            domain: value.domain,
            tier: value.tier,
            entries: value
                .entries
                .into_iter()
                .map(|entry| MpackLogEntry {
                    timestamp: entry.timestamp,
                    level: entry.level,
                    message: entry.message,
                    request_id: entry.request_id,
                    metadata: MpackLogMetadata {
                        status: entry.metadata.status,
                        duration_ms: entry.metadata.duration_ms,
                        bytes_sent: entry.metadata.bytes_sent,
                        user_agent: entry.metadata.user_agent,
                        remote_addr: entry.metadata.remote_addr,
                    },
                })
                .collect(),
        }),
        Dataset::Profile(value) => PreparedMpack::Profile(MpackProfileDataset {
            version: value.version,
            domain: value.domain,
            tier: value.tier,
            profiles: value
                .profiles
                .into_iter()
                .map(|profile| MpackProfile {
                    id: profile.id,
                    name: profile.name,
                    email: profile.email,
                    active: profile.active,
                    tags: profile.tags,
                    preferences: MpackProfilePreferences {
                        locale: profile.preferences.locale,
                        newsletter: profile.preferences.newsletter,
                        theme: profile.preferences.theme,
                    },
                    address: MpackProfileAddress {
                        city: profile.address.city,
                        postal_code: profile.address.postal_code,
                        country: profile.address.country,
                    },
                })
                .collect(),
        }),
        Dataset::Mesh(value) => PreparedMpack::Mesh(MpackMeshDataset {
            version: value.version,
            domain: value.domain,
            tier: value.tier,
            name: value.name,
            vertices: value
                .vertices
                .into_iter()
                .map(|vertex| MpackVertex {
                    x: vertex.x,
                    y: vertex.y,
                    z: vertex.z,
                    nx: vertex.nx,
                    ny: vertex.ny,
                    nz: vertex.nz,
                })
                .collect(),
            indices: value.indices,
        }),
        Dataset::Catalog(value) => PreparedMpack::Catalog(MpackCatalogDataset {
            version: value.version,
            domain: value.domain,
            tier: value.tier,
            products: value
                .products
                .into_iter()
                .map(|product| MpackProduct {
                    sku: product.sku,
                    name: product.name,
                    price_cents: product.price_cents,
                    currency: product.currency,
                    in_stock: product.in_stock,
                    tags: product.tags,
                    attributes: product.attributes,
                })
                .collect(),
        }),
    }
}

pub fn encode(prepared: &PreparedMpack) -> Vec<u8> {
    match prepared {
        PreparedMpack::Logs(value) => value.pack_to_vec(),
        PreparedMpack::Profile(value) => value.pack_to_vec(),
        PreparedMpack::Mesh(value) => value.pack_to_vec(),
        PreparedMpack::Catalog(value) => value.pack_to_vec(),
    }
}
