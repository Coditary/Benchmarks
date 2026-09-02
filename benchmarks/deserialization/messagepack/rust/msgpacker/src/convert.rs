use std::collections::BTreeMap;

use bench_support::dataset::Dataset;
use bench_support::deserialize::DecodedDataset;
use msgpacker::{MsgPacker, Packable, Unpackable};

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


pub fn decode(spec: &str, bytes: &[u8]) -> DecodedDataset {
    use bench_support::shared::domain_from_spec;

    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(from_logs(MpackLogDataset::unpack(bytes).expect("decode"))),
        "profile" => DecodedDataset::Profile(from_profile(
            MpackProfileDataset::unpack(bytes).expect("decode"),
        )),
        "mesh" => DecodedDataset::Mesh(from_mesh(MpackMeshDataset::unpack(bytes).expect("decode"))),
        "catalog" => DecodedDataset::Catalog(from_catalog(
            MpackCatalogDataset::unpack(bytes).expect("decode"),
        )),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn from_logs(value: MpackLogDataset) -> bench_support::logs::LogDataset {
    bench_support::logs::LogDataset {
        version: value.version,
        domain: value.domain,
        tier: value.tier,
        entries: value
            .entries
            .into_iter()
            .map(|entry| bench_support::logs::LogEntry {
                timestamp: entry.timestamp,
                level: entry.level,
                message: entry.message,
                request_id: entry.request_id,
                metadata: bench_support::logs::LogMetadata {
                    status: entry.metadata.status,
                    duration_ms: entry.metadata.duration_ms,
                    bytes_sent: entry.metadata.bytes_sent,
                    user_agent: entry.metadata.user_agent,
                    remote_addr: entry.metadata.remote_addr,
                },
            })
            .collect(),
    }
}

fn from_profile(value: MpackProfileDataset) -> bench_support::profile::ProfileDataset {
    bench_support::profile::ProfileDataset {
        version: value.version,
        domain: value.domain,
        tier: value.tier,
        profiles: value
            .profiles
            .into_iter()
            .map(|profile| bench_support::profile::Profile {
                id: profile.id,
                name: profile.name,
                email: profile.email,
                active: profile.active,
                tags: profile.tags,
                preferences: bench_support::profile::ProfilePreferences {
                    locale: profile.preferences.locale,
                    newsletter: profile.preferences.newsletter,
                    theme: profile.preferences.theme,
                },
                address: bench_support::profile::ProfileAddress {
                    city: profile.address.city,
                    postal_code: profile.address.postal_code,
                    country: profile.address.country,
                },
            })
            .collect(),
    }
}

fn from_mesh(value: MpackMeshDataset) -> bench_support::mesh::MeshDataset {
    bench_support::mesh::MeshDataset {
        version: value.version,
        domain: value.domain,
        tier: value.tier,
        name: value.name,
        vertices: value
            .vertices
            .into_iter()
            .map(|vertex| bench_support::mesh::Vertex {
                x: vertex.x,
                y: vertex.y,
                z: vertex.z,
                nx: vertex.nx,
                ny: vertex.ny,
                nz: vertex.nz,
            })
            .collect(),
        indices: value.indices,
    }
}

fn from_catalog(value: MpackCatalogDataset) -> bench_support::catalog::CatalogDataset {
    bench_support::catalog::CatalogDataset {
        version: value.version,
        domain: value.domain,
        tier: value.tier,
        products: value
            .products
            .into_iter()
            .map(|product| bench_support::catalog::Product {
                sku: product.sku,
                name: product.name,
                price_cents: product.price_cents,
                currency: product.currency,
                in_stock: product.in_stock,
                tags: product.tags,
                attributes: product.attributes,
            })
            .collect(),
    }
}
