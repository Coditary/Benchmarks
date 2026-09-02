use bench_support::ast::{AstDataset, AstNode};
use bench_support::catalog::CatalogDataset;
use bench_support::dataset::Dataset;
use bench_support::logs::{LogDataset, LogEntry, LogMetadata};
use bench_support::mesh::MeshDataset;
use bench_support::profile::ProfileDataset;
use flatbuffers::FlatBufferBuilder;

mod benchmark_generated {
    include!(concat!(env!("OUT_DIR"), "/benchmark_generated.rs"));
}

use benchmark_generated::benchmark::{
    AstDataset as FbAstDataset, AstDatasetArgs, AstNode as FbAstNode, AstNodeArgs,
    AstSpan as FbAstSpan, AstSpanArgs, CatalogDataset as FbCatalogDataset, CatalogDatasetArgs,
    KeyValue, KeyValueArgs, LogDataset as FbLogDataset, LogDatasetArgs, LogEntry as FbLogEntry,
    LogEntryArgs, LogMetadata as FbLogMetadata, LogMetadataArgs, MeshDataset as FbMeshDataset,
    MeshDatasetArgs, Product as FbProduct, ProductArgs, Profile as FbProfile,
    ProfileAddress as FbProfileAddress, ProfileAddressArgs, ProfileDataset as FbProfileDataset,
    ProfileDatasetArgs, ProfilePreferences as FbProfilePreferences, ProfilePreferencesArgs,
    ProfileArgs, Vertex as FbVertex, VertexArgs,
};

pub fn serialize(data: &Dataset) -> Vec<u8> {
    match data {
        Dataset::Logs(value) => serialize_logs(value),
        Dataset::Profile(value) => serialize_profile(value),
        Dataset::Mesh(value) => serialize_mesh(value),
        Dataset::Catalog(value) => serialize_catalog(value),
        Dataset::Ast(value) => serialize_ast(value),
    }
}

fn serialize_logs(data: &LogDataset) -> Vec<u8> {
    let mut builder = FlatBufferBuilder::with_capacity(1024);
    let mut entry_offsets = Vec::with_capacity(data.entries.len());

    for entry in &data.entries {
        entry_offsets.push(build_log_entry(&mut builder, entry));
    }

    let entries = builder.create_vector(&entry_offsets);
    let domain = builder.create_string(&data.domain);
    let tier = builder.create_string(&data.tier);
    let root = FbLogDataset::create(
        &mut builder,
        &LogDatasetArgs {
            version: data.version,
            domain: Some(domain),
            tier: Some(tier),
            entries: Some(entries),
        },
    );
    builder.finish(root, None);
    builder.finished_data().to_vec()
}

fn serialize_profile(data: &ProfileDataset) -> Vec<u8> {
    let mut builder = FlatBufferBuilder::with_capacity(1024);
    let mut profile_offsets = Vec::with_capacity(data.profiles.len());

    for profile in &data.profiles {
        let id = builder.create_string(&profile.id);
        let name = builder.create_string(&profile.name);
        let email = builder.create_string(&profile.email);
        let mut tag_offsets = Vec::with_capacity(profile.tags.len());
        for tag in &profile.tags {
            tag_offsets.push(builder.create_string(tag));
        }
        let tags = builder.create_vector(&tag_offsets);
        let locale = builder.create_string(&profile.preferences.locale);
        let theme = builder.create_string(&profile.preferences.theme);
        let preferences = FbProfilePreferences::create(
            &mut builder,
            &ProfilePreferencesArgs {
                locale: Some(locale),
                newsletter: profile.preferences.newsletter,
                theme: Some(theme),
            },
        );
        let city = builder.create_string(&profile.address.city);
        let postal_code = builder.create_string(&profile.address.postal_code);
        let country = builder.create_string(&profile.address.country);
        let address = FbProfileAddress::create(
            &mut builder,
            &ProfileAddressArgs {
                city: Some(city),
                postal_code: Some(postal_code),
                country: Some(country),
            },
        );
        profile_offsets.push(FbProfile::create(
            &mut builder,
            &ProfileArgs {
                id: Some(id),
                name: Some(name),
                email: Some(email),
                active: profile.active,
                tags: Some(tags),
                preferences: Some(preferences),
                address: Some(address),
            },
        ));
    }

    let profiles = builder.create_vector(&profile_offsets);
    let domain = builder.create_string(&data.domain);
    let tier = builder.create_string(&data.tier);
    let root = FbProfileDataset::create(
        &mut builder,
        &ProfileDatasetArgs {
            version: data.version,
            domain: Some(domain),
            tier: Some(tier),
            profiles: Some(profiles),
        },
    );
    builder.finish(root, None);
    builder.finished_data().to_vec()
}

fn serialize_mesh(data: &MeshDataset) -> Vec<u8> {
    let mut builder = FlatBufferBuilder::with_capacity(1024);
    let mut vertex_offsets = Vec::with_capacity(data.vertices.len());

    for vertex in &data.vertices {
        vertex_offsets.push(FbVertex::create(
            &mut builder,
            &VertexArgs {
                x: vertex.x,
                y: vertex.y,
                z: vertex.z,
                nx: vertex.nx,
                ny: vertex.ny,
                nz: vertex.nz,
            },
        ));
    }

    let vertices = builder.create_vector(&vertex_offsets);
    let indices = builder.create_vector(&data.indices);
    let domain = builder.create_string(&data.domain);
    let tier = builder.create_string(&data.tier);
    let name = builder.create_string(&data.name);
    let root = FbMeshDataset::create(
        &mut builder,
        &MeshDatasetArgs {
            version: data.version,
            domain: Some(domain),
            tier: Some(tier),
            name: Some(name),
            vertices: Some(vertices),
            indices: Some(indices),
        },
    );
    builder.finish(root, None);
    builder.finished_data().to_vec()
}

fn serialize_catalog(data: &CatalogDataset) -> Vec<u8> {
    let mut builder = FlatBufferBuilder::with_capacity(1024);
    let mut product_offsets = Vec::with_capacity(data.products.len());

    for product in &data.products {
        let sku = builder.create_string(&product.sku);
        let name = builder.create_string(&product.name);
        let currency = builder.create_string(&product.currency);
        let mut tag_offsets = Vec::with_capacity(product.tags.len());
        for tag in &product.tags {
            tag_offsets.push(builder.create_string(tag));
        }
        let tags = builder.create_vector(&tag_offsets);
        let mut attribute_offsets = Vec::with_capacity(product.attributes.len());
        for (key, value) in &product.attributes {
            let key_offset = builder.create_string(key);
            let value_offset = builder.create_string(value);
            attribute_offsets.push(KeyValue::create(
                &mut builder,
                &KeyValueArgs {
                    key: Some(key_offset),
                    value: Some(value_offset),
                },
            ));
        }
        let attributes = builder.create_vector(&attribute_offsets);
        product_offsets.push(FbProduct::create(
            &mut builder,
            &ProductArgs {
                sku: Some(sku),
                name: Some(name),
                price_cents: product.price_cents,
                currency: Some(currency),
                in_stock: product.in_stock,
                tags: Some(tags),
                attributes: Some(attributes),
            },
        ));
    }

    let products = builder.create_vector(&product_offsets);
    let domain = builder.create_string(&data.domain);
    let tier = builder.create_string(&data.tier);
    let root = FbCatalogDataset::create(
        &mut builder,
        &CatalogDatasetArgs {
            version: data.version,
            domain: Some(domain),
            tier: Some(tier),
            products: Some(products),
        },
    );
    builder.finish(root, None);
    builder.finished_data().to_vec()
}

fn serialize_ast(data: &AstDataset) -> Vec<u8> {
    let mut builder = FlatBufferBuilder::with_capacity(1024);
    let mut tree_offsets = Vec::with_capacity(data.trees.len());

    for tree in &data.trees {
        tree_offsets.push(build_ast_node(&mut builder, tree));
    }

    let trees = builder.create_vector(&tree_offsets);
    let domain = builder.create_string(&data.domain);
    let tier = builder.create_string(&data.tier);
    let root = FbAstDataset::create(
        &mut builder,
        &AstDatasetArgs {
            version: data.version,
            domain: Some(domain),
            tier: Some(tier),
            max_depth: data.max_depth,
            trees: Some(trees),
        },
    );
    builder.finish(root, None);
    builder.finished_data().to_vec()
}

fn build_log_entry<'a>(
    builder: &mut FlatBufferBuilder<'a>,
    entry: &LogEntry,
) -> flatbuffers::WIPOffset<FbLogEntry<'a>> {
    let timestamp = builder.create_string(&entry.timestamp);
    let level = builder.create_string(&entry.level);
    let message = builder.create_string(&entry.message);
    let request_id = builder.create_string(&entry.request_id);
    let metadata = build_log_metadata(builder, &entry.metadata);
    FbLogEntry::create(
        builder,
        &LogEntryArgs {
            timestamp: Some(timestamp),
            level: Some(level),
            message: Some(message),
            request_id: Some(request_id),
            metadata: Some(metadata),
        },
    )
}

fn build_log_metadata<'a>(
    builder: &mut FlatBufferBuilder<'a>,
    metadata: &LogMetadata,
) -> flatbuffers::WIPOffset<FbLogMetadata<'a>> {
    let user_agent = builder.create_string(&metadata.user_agent);
    let remote_addr = builder.create_string(&metadata.remote_addr);
    FbLogMetadata::create(
        builder,
        &LogMetadataArgs {
            status: metadata.status,
            duration_ms: metadata.duration_ms,
            bytes_sent: metadata.bytes_sent,
            user_agent: Some(user_agent),
            remote_addr: Some(remote_addr),
        },
    )
}

fn build_ast_node<'a>(
    builder: &mut FlatBufferBuilder<'a>,
    node: &AstNode,
) -> flatbuffers::WIPOffset<FbAstNode<'a>> {
    let node_type = builder.create_string(&node.node_type);
    let name = builder.create_string(&node.name);
    let value = builder.create_string(node.value.as_deref().unwrap_or(""));
    let mut child_offsets = Vec::with_capacity(node.children.len());
    for child in &node.children {
        child_offsets.push(build_ast_node(builder, child));
    }
    let children = builder.create_vector(&child_offsets);
    let span = FbAstSpan::create(
        builder,
        &AstSpanArgs {
            line: node.span.line,
            column: node.span.column,
        },
    );
    FbAstNode::create(
        builder,
        &AstNodeArgs {
            node_type: Some(node_type),
            id: node.id,
            name: Some(name),
            span: Some(span),
            value: Some(value),
            children: Some(children),
        },
    )
}
