use bench_support::ast::{AstDataset, AstNode, AstSpan};
use bench_support::catalog::CatalogDataset;
use bench_support::dataset::Dataset;
use bench_support::deserialize::DecodedDataset;
use bench_support::logs::LogDataset;
use bench_support::mesh::MeshDataset;
use bench_support::profile::ProfileDataset;
use prost::Message;

pub mod bench {
    include!(concat!(env!("OUT_DIR"), "/bench.rs"));
}

pub enum PreparedProst {
    Logs(bench::LogDataset),
    Profile(bench::ProfileDataset),
    Mesh(bench::MeshDataset),
    Catalog(bench::CatalogDataset),
    Ast(bench::AstDataset),
}

pub fn prepare(data: Dataset) -> PreparedProst {
    match data {
        Dataset::Logs(value) => PreparedProst::Logs(to_logs(&value)),
        Dataset::Profile(value) => PreparedProst::Profile(to_profile(&value)),
        Dataset::Mesh(value) => PreparedProst::Mesh(to_mesh(&value)),
        Dataset::Catalog(value) => PreparedProst::Catalog(to_catalog(&value)),
        Dataset::Ast(value) => PreparedProst::Ast(to_ast(&value)),
    }
}

pub fn encode(prepared: &PreparedProst) -> Vec<u8> {
    let mut buffer = Vec::new();
    match prepared {
        PreparedProst::Logs(value) => value.encode(&mut buffer).expect("serialize output"),
        PreparedProst::Profile(value) => value.encode(&mut buffer).expect("serialize output"),
        PreparedProst::Mesh(value) => value.encode(&mut buffer).expect("serialize output"),
        PreparedProst::Catalog(value) => value.encode(&mut buffer).expect("serialize output"),
        PreparedProst::Ast(value) => value.encode(&mut buffer).expect("serialize output"),
    }
    buffer
}

fn to_logs(data: &LogDataset) -> bench::LogDataset {
    bench::LogDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        entries: data
            .entries
            .iter()
            .map(|entry| bench::LogEntry {
                timestamp: entry.timestamp.clone(),
                level: entry.level.clone(),
                message: entry.message.clone(),
                request_id: entry.request_id.clone(),
                metadata: Some(bench::LogMetadata {
                    status: entry.metadata.status as u32,
                    duration_ms: entry.metadata.duration_ms,
                    bytes_sent: entry.metadata.bytes_sent,
                    user_agent: entry.metadata.user_agent.clone(),
                    remote_addr: entry.metadata.remote_addr.clone(),
                }),
            })
            .collect(),
    }
}

fn to_profile(data: &ProfileDataset) -> bench::ProfileDataset {
    bench::ProfileDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        profiles: data
            .profiles
            .iter()
            .map(|profile| bench::Profile {
                id: profile.id.clone(),
                name: profile.name.clone(),
                email: profile.email.clone(),
                active: profile.active,
                tags: profile.tags.clone(),
                preferences: Some(bench::ProfilePreferences {
                    locale: profile.preferences.locale.clone(),
                    newsletter: profile.preferences.newsletter,
                    theme: profile.preferences.theme.clone(),
                }),
                address: Some(bench::ProfileAddress {
                    city: profile.address.city.clone(),
                    postal_code: profile.address.postal_code.clone(),
                    country: profile.address.country.clone(),
                }),
            })
            .collect(),
    }
}

fn to_mesh(data: &MeshDataset) -> bench::MeshDataset {
    bench::MeshDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        name: data.name.clone(),
        vertices: data
            .vertices
            .iter()
            .map(|vertex| bench::Vertex {
                x: vertex.x,
                y: vertex.y,
                z: vertex.z,
                nx: vertex.nx,
                ny: vertex.ny,
                nz: vertex.nz,
            })
            .collect(),
        indices: data.indices.clone(),
    }
}

fn to_catalog(data: &CatalogDataset) -> bench::CatalogDataset {
    bench::CatalogDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        products: data
            .products
            .iter()
            .map(|product| bench::Product {
                sku: product.sku.clone(),
                name: product.name.clone(),
                price_cents: product.price_cents,
                currency: product.currency.clone(),
                in_stock: product.in_stock,
                tags: product.tags.clone(),
                attributes: product
                    .attributes
                    .iter()
                    .map(|(key, value)| (key.clone(), value.clone()))
                    .collect(),
            })
            .collect(),
    }
}

fn to_ast_node(node: &AstNode) -> bench::AstNode {
    bench::AstNode {
        node_type: node.node_type.clone(),
        id: node.id,
        name: node.name.clone(),
        span: Some(bench::AstSpan {
            line: node.span.line,
            column: node.span.column,
        }),
        value: node.value.clone(),
        children: node
            .children
            .iter()
            .map(|child| to_ast_node(child))
            .collect(),
    }
}

fn to_ast(data: &AstDataset) -> bench::AstDataset {
    bench::AstDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        max_depth: data.max_depth,
        trees: data.trees.iter().map(to_ast_node).collect(),
    }
}

fn from_ast_node(node: &bench::AstNode) -> AstNode {
    let span = node.span.as_ref();
    AstNode {
        node_type: node.node_type.clone(),
        id: node.id,
        name: node.name.clone(),
        span: AstSpan {
            line: span.map(|value| value.line).unwrap_or(0),
            column: span.map(|value| value.column).unwrap_or(0),
        },
        value: node.value.clone(),
        children: node
            .children
            .iter()
            .map(|child| Box::new(from_ast_node(child)))
            .collect(),
    }
}

fn from_ast(data: &bench::AstDataset) -> AstDataset {
    AstDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        max_depth: data.max_depth,
        trees: data.trees.iter().map(from_ast_node).collect(),
    }
}


pub fn decode(spec: &str, bytes: &[u8]) -> DecodedDataset {
    use bench_support::shared::domain_from_spec;

    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(from_logs(
            &bench::LogDataset::decode(bytes).expect("decode"),
        )),
        "profile" => DecodedDataset::Profile(from_profile(
            &bench::ProfileDataset::decode(bytes).expect("decode"),
        )),
        "mesh" => DecodedDataset::Mesh(from_mesh(
            &bench::MeshDataset::decode(bytes).expect("decode"),
        )),
        "catalog" => DecodedDataset::Catalog(from_catalog(
            &bench::CatalogDataset::decode(bytes).expect("decode"),
        )),
        "ast" => DecodedDataset::Ast(from_ast(
            &bench::AstDataset::decode(bytes).expect("decode"),
        )),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn from_logs(data: &bench::LogDataset) -> LogDataset {
    LogDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        entries: data
            .entries
            .iter()
            .map(|entry| bench_support::logs::LogEntry {
                timestamp: entry.timestamp.clone(),
                level: entry.level.clone(),
                message: entry.message.clone(),
                request_id: entry.request_id.clone(),
                metadata: bench_support::logs::LogMetadata {
                    status: entry.metadata.as_ref().map(|m| m.status as u16).unwrap_or(0),
                    duration_ms: entry.metadata.as_ref().map(|m| m.duration_ms).unwrap_or(0),
                    bytes_sent: entry.metadata.as_ref().map(|m| m.bytes_sent).unwrap_or(0),
                    user_agent: entry
                        .metadata
                        .as_ref()
                        .map(|m| m.user_agent.clone())
                        .unwrap_or_default(),
                    remote_addr: entry
                        .metadata
                        .as_ref()
                        .map(|m| m.remote_addr.clone())
                        .unwrap_or_default(),
                },
            })
            .collect(),
    }
}

fn from_profile(data: &bench::ProfileDataset) -> ProfileDataset {
    ProfileDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        profiles: data
            .profiles
            .iter()
            .map(|profile| bench_support::profile::Profile {
                id: profile.id.clone(),
                name: profile.name.clone(),
                email: profile.email.clone(),
                active: profile.active,
                tags: profile.tags.clone(),
                preferences: bench_support::profile::ProfilePreferences {
                    locale: profile
                        .preferences
                        .as_ref()
                        .map(|p| p.locale.clone())
                        .unwrap_or_default(),
                    newsletter: profile
                        .preferences
                        .as_ref()
                        .map(|p| p.newsletter)
                        .unwrap_or_default(),
                    theme: profile
                        .preferences
                        .as_ref()
                        .map(|p| p.theme.clone())
                        .unwrap_or_default(),
                },
                address: bench_support::profile::ProfileAddress {
                    city: profile
                        .address
                        .as_ref()
                        .map(|a| a.city.clone())
                        .unwrap_or_default(),
                    postal_code: profile
                        .address
                        .as_ref()
                        .map(|a| a.postal_code.clone())
                        .unwrap_or_default(),
                    country: profile
                        .address
                        .as_ref()
                        .map(|a| a.country.clone())
                        .unwrap_or_default(),
                },
            })
            .collect(),
    }
}

fn from_mesh(data: &bench::MeshDataset) -> MeshDataset {
    MeshDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        name: data.name.clone(),
        vertices: data
            .vertices
            .iter()
            .map(|vertex| bench_support::mesh::Vertex {
                x: vertex.x,
                y: vertex.y,
                z: vertex.z,
                nx: vertex.nx,
                ny: vertex.ny,
                nz: vertex.nz,
            })
            .collect(),
        indices: data.indices.clone(),
    }
}

fn from_catalog(data: &bench::CatalogDataset) -> CatalogDataset {
    CatalogDataset {
        version: data.version,
        domain: data.domain.clone(),
        tier: data.tier.clone(),
        products: data
            .products
            .iter()
            .map(|product| bench_support::catalog::Product {
                sku: product.sku.clone(),
                name: product.name.clone(),
                price_cents: product.price_cents,
                currency: product.currency.clone(),
                in_stock: product.in_stock,
                tags: product.tags.clone(),
                attributes: product.attributes.clone().into_iter().collect(),
            })
            .collect(),
    }
}
