use crate::ast::{AstDataset, AstNode, AstSpan};
use crate::catalog::{CatalogDataset, Product};
use crate::deserialize::DecodedDataset;
use crate::dataset::Dataset;
use crate::logs::{LogDataset, LogEntry, LogMetadata};
use crate::mesh::{MeshDataset, Vertex};
use crate::profile::{Profile, ProfileAddress, ProfileDataset, ProfilePreferences};
use crate::shared::domain_from_spec;

pub fn encode(data: &Dataset) -> Vec<u8> {
    let text = match data {
        Dataset::Logs(value) => encode_logs(value),
        Dataset::Profile(value) => encode_profile(value),
        Dataset::Mesh(value) => encode_mesh(value),
        Dataset::Catalog(value) => encode_catalog(value),
        Dataset::Ast(value) => encode_ast(value),
    };
    text.into_bytes()
}

pub fn decode(spec: &str, bytes: &[u8]) -> DecodedDataset {
    let input = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(decode_logs(input)),
        "profile" => DecodedDataset::Profile(decode_profile(input)),
        "mesh" => DecodedDataset::Mesh(decode_mesh(input)),
        "catalog" => DecodedDataset::Catalog(decode_catalog(input)),
        "ast" => DecodedDataset::Ast(decode_ast(input)),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn open_tag(out: &mut String, name: &str) {
    out.push('<');
    out.push_str(name);
    out.push('>');
}

fn close_tag(out: &mut String, name: &str) {
    out.push_str("</");
    out.push_str(name);
    out.push('>');
}

fn write_node_text(out: &mut String, name: &str, value: &str) {
    open_tag(out, name);
    out.push_str(&escape_xml(value));
    close_tag(out, name);
}

fn write_u64(out: &mut String, name: &str, value: u64) {
    write_node_text(out, name, &value.to_string());
}

fn write_bool(out: &mut String, name: &str, value: bool) {
    write_node_text(out, name, if value { "true" } else { "false" });
}

fn encode_metadata(out: &mut String, metadata: &LogMetadata) {
    open_tag(out, "metadata");
    write_u64(out, "status", metadata.status as u64);
    write_u64(out, "duration_ms", metadata.duration_ms as u64);
    write_u64(out, "bytes_sent", metadata.bytes_sent as u64);
    write_node_text(out, "user_agent", &metadata.user_agent);
    write_node_text(out, "remote_addr", &metadata.remote_addr);
    close_tag(out, "metadata");
}

fn encode_logs(data: &LogDataset) -> String {
    let mut out = String::from("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
    open_tag(&mut out, "LogDataset");
    write_u64(&mut out, "version", data.version as u64);
    write_node_text(&mut out, "domain", &data.domain);
    write_node_text(&mut out, "tier", &data.tier);
    open_tag(&mut out, "entries");
    for entry in &data.entries {
        open_tag(&mut out, "LogEntry");
        write_node_text(&mut out, "timestamp", &entry.timestamp);
        write_node_text(&mut out, "level", &entry.level);
        write_node_text(&mut out, "message", &entry.message);
        write_node_text(&mut out, "request_id", &entry.request_id);
        encode_metadata(&mut out, &entry.metadata);
        close_tag(&mut out, "LogEntry");
    }
    close_tag(&mut out, "entries");
    close_tag(&mut out, "LogDataset");
    out
}

fn encode_profile(data: &ProfileDataset) -> String {
    let mut out = String::from("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
    open_tag(&mut out, "ProfileDataset");
    write_u64(&mut out, "version", data.version as u64);
    write_node_text(&mut out, "domain", &data.domain);
    write_node_text(&mut out, "tier", &data.tier);
    open_tag(&mut out, "profiles");
    for profile in &data.profiles {
        open_tag(&mut out, "Profile");
        write_node_text(&mut out, "id", &profile.id);
        write_node_text(&mut out, "name", &profile.name);
        write_node_text(&mut out, "email", &profile.email);
        write_bool(&mut out, "active", profile.active);
        open_tag(&mut out, "tags");
        for tag in &profile.tags {
            write_node_text(&mut out, "tag", tag);
        }
        close_tag(&mut out, "tags");
        open_tag(&mut out, "preferences");
        write_node_text(&mut out, "locale", &profile.preferences.locale);
        write_bool(&mut out, "newsletter", profile.preferences.newsletter);
        write_node_text(&mut out, "theme", &profile.preferences.theme);
        close_tag(&mut out, "preferences");
        open_tag(&mut out, "address");
        write_node_text(&mut out, "city", &profile.address.city);
        write_node_text(&mut out, "postal_code", &profile.address.postal_code);
        write_node_text(&mut out, "country", &profile.address.country);
        close_tag(&mut out, "address");
        close_tag(&mut out, "Profile");
    }
    close_tag(&mut out, "profiles");
    close_tag(&mut out, "ProfileDataset");
    out
}

fn encode_mesh(data: &MeshDataset) -> String {
    let mut out = String::from("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
    open_tag(&mut out, "MeshDataset");
    write_u64(&mut out, "version", data.version as u64);
    write_node_text(&mut out, "domain", &data.domain);
    write_node_text(&mut out, "tier", &data.tier);
    write_node_text(&mut out, "name", &data.name);
    open_tag(&mut out, "vertices");
    for vertex in &data.vertices {
        open_tag(&mut out, "Vertex");
        for (key, value) in [
            ("x", vertex.x.to_string()),
            ("y", vertex.y.to_string()),
            ("z", vertex.z.to_string()),
            ("nx", vertex.nx.to_string()),
            ("ny", vertex.ny.to_string()),
            ("nz", vertex.nz.to_string()),
        ] {
            write_node_text(&mut out, key, &value);
        }
        close_tag(&mut out, "Vertex");
    }
    close_tag(&mut out, "vertices");
    open_tag(&mut out, "indices");
    for index in &data.indices {
        write_u64(&mut out, "index", *index as u64);
    }
    close_tag(&mut out, "indices");
    close_tag(&mut out, "MeshDataset");
    out
}

fn encode_catalog(data: &CatalogDataset) -> String {
    let mut out = String::from("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
    open_tag(&mut out, "CatalogDataset");
    write_u64(&mut out, "version", data.version as u64);
    write_node_text(&mut out, "domain", &data.domain);
    write_node_text(&mut out, "tier", &data.tier);
    open_tag(&mut out, "products");
    for product in &data.products {
        open_tag(&mut out, "Product");
        write_node_text(&mut out, "sku", &product.sku);
        write_node_text(&mut out, "name", &product.name);
        write_u64(&mut out, "price_cents", product.price_cents as u64);
        write_node_text(&mut out, "currency", &product.currency);
        write_bool(&mut out, "in_stock", product.in_stock);
        open_tag(&mut out, "tags");
        for tag in &product.tags {
            write_node_text(&mut out, "tag", tag);
        }
        close_tag(&mut out, "tags");
        if !product.attributes.is_empty() {
            open_tag(&mut out, "attributes");
            for (key, value) in &product.attributes {
                write_node_text(&mut out, key, value);
            }
            close_tag(&mut out, "attributes");
        }
        close_tag(&mut out, "Product");
    }
    close_tag(&mut out, "products");
    close_tag(&mut out, "CatalogDataset");
    out
}

fn encode_ast_span(out: &mut String, span: &AstSpan) {
    open_tag(out, "span");
    write_u64(out, "line", span.line as u64);
    write_u64(out, "column", span.column as u64);
    close_tag(out, "span");
}

fn encode_ast_node(out: &mut String, node: &AstNode) {
    open_tag(out, "AstNode");
    write_node_text(out, "node_type", &node.node_type);
    write_u64(out, "id", node.id);
    write_node_text(out, "name", &node.name);
    encode_ast_span(out, &node.span);
    if let Some(value) = &node.value {
        write_node_text(out, "value", value);
    }
    if !node.children.is_empty() {
        open_tag(out, "children");
        for child in &node.children {
            encode_ast_node(out, child);
        }
        close_tag(out, "children");
    }
    close_tag(out, "AstNode");
}

fn encode_ast(data: &AstDataset) -> String {
    let mut out = String::from("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
    open_tag(&mut out, "AstDataset");
    write_u64(&mut out, "version", data.version as u64);
    write_node_text(&mut out, "domain", &data.domain);
    write_node_text(&mut out, "tier", &data.tier);
    write_u64(&mut out, "max_depth", data.max_depth as u64);
    open_tag(&mut out, "trees");
    for tree in &data.trees {
        encode_ast_node(&mut out, tree);
    }
    close_tag(&mut out, "trees");
    close_tag(&mut out, "AstDataset");
    out
}

#[derive(Debug)]
struct XmlNode {
    name: String,
    text: Option<String>,
    children: Vec<XmlNode>,
}

fn parse_xml(input: &str) -> XmlNode {
    let mut index = 0;
    let bytes = input.as_bytes();
    fn skip_ws(bytes: &[u8], index: &mut usize) {
        while *index < bytes.len() && bytes[*index].is_ascii_whitespace() {
            *index += 1;
        }
    }
    fn read_name(bytes: &[u8], index: &mut usize) -> String {
        let start = *index;
        while *index < bytes.len() && !matches!(bytes[*index], b' ' | b'>' | b'/' | b'\t' | b'\n' | b'\r') {
            *index += 1;
        }
        String::from_utf8(bytes[start..*index].to_vec()).expect("utf8")
    }
    fn parse_node(bytes: &[u8], index: &mut usize) -> XmlNode {
        skip_ws(bytes, index);
        if bytes[*index] != b'<' {
            panic!("expected <");
        }
        *index += 1;
        if bytes[*index] == b'?' || bytes[*index] == b'!' {
            while *index < bytes.len() && !(bytes[*index] == b'>' && bytes.get(*index - 1) == Some(&b'?')) {
                *index += 1;
            }
            *index += 1;
            return parse_node(bytes, index);
        }
        let name = read_name(bytes, index);
        skip_ws(bytes, index);
        if bytes[*index] == b'/' {
            *index += 2;
            return XmlNode {
                name,
                text: None,
                children: Vec::new(),
            };
        }
        if bytes[*index] != b'>' {
            panic!("expected >");
        }
        *index += 1;
        let mut children = Vec::new();
        let mut content = String::new();
        loop {
            skip_ws(bytes, index);
            if *index >= bytes.len() {
                break;
            }
            if bytes[*index] == b'<' {
                if bytes.get(*index + 1) == Some(&b'/') {
                    *index += 2;
                    let end_name = read_name(bytes, index);
                    assert_eq!(end_name, name);
                    if bytes[*index] != b'>' {
                        panic!("expected >");
                    }
                    *index += 1;
                    break;
                }
                children.push(parse_node(bytes, index));
                continue;
            }
            let start = *index;
            while *index < bytes.len() && bytes[*index] != b'<' {
                *index += 1;
            }
            content.push_str(&String::from_utf8(bytes[start..*index].to_vec()).expect("utf8"));
        }
        let text = if content.trim().is_empty() {
            None
        } else {
            Some(content.trim().to_string())
        };
        XmlNode {
            name,
            text,
            children,
        }
    }
    parse_node(bytes, &mut index)
}

fn child<'a>(node: &'a XmlNode, name: &str) -> &'a XmlNode {
    node.children
        .iter()
        .find(|child| child.name == name)
        .unwrap_or_else(|| panic!("missing child {name}"))
}

fn children<'a>(node: &'a XmlNode, name: &str) -> Vec<&'a XmlNode> {
    node.children.iter().filter(|child| child.name == name).collect()
}

fn node_text(node: &XmlNode) -> String {
    node.text.clone().unwrap_or_default()
}

fn node_text_u32(node: &XmlNode) -> u32 {
    node_text(node).parse().expect("u32")
}

fn node_text_u16(node: &XmlNode) -> u16 {
    node_text_u32(node) as u16
}

fn node_text_bool(node: &XmlNode) -> bool {
    matches!(node_text(node).as_str(), "true" | "1")
}

fn node_text_f32(node: &XmlNode) -> f32 {
    node_text(node).parse().expect("f32")
}

fn decode_logs(input: &str) -> LogDataset {
    let root = parse_xml(input);
    let entries = children(&child(&root, "entries"), "LogEntry")
        .into_iter()
        .map(|entry| {
            let metadata = child(entry, "metadata");
            LogEntry {
                timestamp: node_text(child(entry, "timestamp")),
                level: node_text(child(entry, "level")),
                message: node_text(child(entry, "message")),
                request_id: node_text(child(entry, "request_id")),
                metadata: LogMetadata {
                    status: node_text_u16(child(metadata, "status")),
                    duration_ms: node_text_u32(child(metadata, "duration_ms")),
                    bytes_sent: node_text_u32(child(metadata, "bytes_sent")),
                    user_agent: node_text(child(metadata, "user_agent")),
                    remote_addr: node_text(child(metadata, "remote_addr")),
                },
            }
        })
        .collect();
    LogDataset {
        version: node_text_u32(child(&root, "version")),
        domain: node_text(child(&root, "domain")),
        tier: node_text(child(&root, "tier")),
        entries,
    }
}

fn decode_profile(input: &str) -> ProfileDataset {
    let root = parse_xml(input);
    let profiles = children(&child(&root, "profiles"), "Profile")
        .into_iter()
        .map(|profile| {
            let prefs = child(profile, "preferences");
            let address = child(profile, "address");
            let tags = children(&child(profile, "tags"), "tag")
                .into_iter()
                .map(node_text)
                .collect();
            Profile {
                id: node_text(child(profile, "id")),
                name: node_text(child(profile, "name")),
                email: node_text(child(profile, "email")),
                active: node_text_bool(child(profile, "active")),
                tags,
                preferences: ProfilePreferences {
                    locale: node_text(child(prefs, "locale")),
                    newsletter: node_text_bool(child(prefs, "newsletter")),
                    theme: node_text(child(prefs, "theme")),
                },
                address: ProfileAddress {
                    city: node_text(child(address, "city")),
                    postal_code: node_text(child(address, "postal_code")),
                    country: node_text(child(address, "country")),
                },
            }
        })
        .collect();
    ProfileDataset {
        version: node_text_u32(child(&root, "version")),
        domain: node_text(child(&root, "domain")),
        tier: node_text(child(&root, "tier")),
        profiles,
    }
}

fn decode_mesh(input: &str) -> MeshDataset {
    let root = parse_xml(input);
    let vertices = children(&child(&root, "vertices"), "Vertex")
        .into_iter()
        .map(|vertex| Vertex {
            x: node_text_f32(child(vertex, "x")),
            y: node_text_f32(child(vertex, "y")),
            z: node_text_f32(child(vertex, "z")),
            nx: node_text_f32(child(vertex, "nx")),
            ny: node_text_f32(child(vertex, "ny")),
            nz: node_text_f32(child(vertex, "nz")),
        })
        .collect();
    let indices = children(&child(&root, "indices"), "index")
        .into_iter()
        .map(node_text_u32)
        .collect();
    MeshDataset {
        version: node_text_u32(child(&root, "version")),
        domain: node_text(child(&root, "domain")),
        tier: node_text(child(&root, "tier")),
        name: node_text(child(&root, "name")),
        vertices,
        indices,
    }
}

fn decode_catalog(input: &str) -> CatalogDataset {
    let root = parse_xml(input);
    let products = children(&child(&root, "products"), "Product")
        .into_iter()
        .map(|product| {
            let tags = children(&child(product, "tags"), "tag")
                .into_iter()
                .map(node_text)
                .collect();
            let mut attributes = std::collections::BTreeMap::new();
            if let Some(attrs) = product.children.iter().find(|node| node.name == "attributes") {
                for child in &attrs.children {
                    attributes.insert(child.name.clone(), node_text(child));
                }
            }
            Product {
                sku: node_text(child(product, "sku")),
                name: node_text(child(product, "name")),
                price_cents: node_text_u32(child(product, "price_cents")),
                currency: node_text(child(product, "currency")),
                in_stock: node_text_bool(child(product, "in_stock")),
                tags,
                attributes,
            }
        })
        .collect();
    CatalogDataset {
        version: node_text_u32(child(&root, "version")),
        domain: node_text(child(&root, "domain")),
        tier: node_text(child(&root, "tier")),
        products,
    }
}

fn node_text_u64(node: &XmlNode) -> u64 {
    node_text(node).parse().expect("u64")
}

fn decode_ast_node(node: &XmlNode) -> AstNode {
    let children = if let Some(children_node) = node.children.iter().find(|child| child.name == "children") {
        children(children_node, "AstNode")
            .into_iter()
            .map(|child| Box::new(decode_ast_node(child)))
            .collect()
    } else {
        Vec::new()
    };
    AstNode {
        node_type: node_text(child(node, "node_type")),
        id: node_text_u64(child(node, "id")),
        name: node_text(child(node, "name")),
        span: AstSpan {
            line: node_text_u32(child(child(node, "span"), "line")),
            column: node_text_u32(child(child(node, "span"), "column")),
        },
        value: node
            .children
            .iter()
            .find(|child| child.name == "value")
            .map(node_text),
        children,
    }
}

fn decode_ast(input: &str) -> AstDataset {
    let root = parse_xml(input);
    let trees = children(&child(&root, "trees"), "AstNode")
        .into_iter()
        .map(decode_ast_node)
        .collect();
    AstDataset {
        version: node_text_u32(child(&root, "version")),
        domain: node_text(child(&root, "domain")),
        tier: node_text(child(&root, "tier")),
        max_depth: node_text_u32(child(&root, "max_depth")),
        trees,
    }
}
