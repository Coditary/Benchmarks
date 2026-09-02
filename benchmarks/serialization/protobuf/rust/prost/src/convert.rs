use bench_support::ast::{AstDataset, AstNode};
use bench_support::catalog::CatalogDataset;
use bench_support::dataset::Dataset;
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
