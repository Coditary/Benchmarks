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
    };
    text.into_bytes()
}

pub fn decode(spec: &str, bytes: &[u8]) -> DecodedDataset {
    let text = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(decode_logs(text)),
        "profile" => DecodedDataset::Profile(decode_profile(text)),
        "mesh" => DecodedDataset::Mesh(decode_mesh(text)),
        "catalog" => DecodedDataset::Catalog(decode_catalog(text)),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn quote(value: &str) -> String {
    format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
}

fn push_arg(out: &mut String, value: &str) {
    out.push(' ');
    out.push_str(&quote(value));
}

fn push_int(out: &mut String, value: impl std::fmt::Display) {
    out.push(' ');
    out.push_str(&value.to_string());
}

fn push_bool(out: &mut String, value: bool) {
    push_int(out, if value { "true" } else { "false" });
}

fn push_block(out: &mut String, name: &str, body: &str) {
    out.push_str(name);
    out.push_str(" {");
  out.push('\n');
    out.push_str(body);
    out.push_str("}\n");
}

fn encode_metadata(metadata: &LogMetadata) -> String {
    let mut inner = String::new();
    inner.push_str("status");
    push_int(&mut inner, metadata.status);
    inner.push('\n');
    inner.push_str("duration_ms");
    push_int(&mut inner, metadata.duration_ms);
    inner.push('\n');
    inner.push_str("bytes_sent");
    push_int(&mut inner, metadata.bytes_sent);
    inner.push('\n');
    inner.push_str("user_agent");
    push_arg(&mut inner, &metadata.user_agent);
    inner.push('\n');
    inner.push_str("remote_addr");
    push_arg(&mut inner, &metadata.remote_addr);
    inner.push('\n');
    let mut out = String::new();
    push_block(&mut out, "metadata", &inner);
    out
}

fn encode_logs(data: &LogDataset) -> String {
    let mut out = String::new();
    out.push_str("version");
    push_int(&mut out, data.version);
    out.push('\n');
    out.push_str("domain");
    push_arg(&mut out, &data.domain);
    out.push('\n');
    out.push_str("tier");
    push_arg(&mut out, &data.tier);
    out.push('\n');
    let mut entries = String::new();
    for entry in &data.entries {
        let mut body = String::new();
        body.push_str("timestamp");
        push_arg(&mut body, &entry.timestamp);
        body.push('\n');
        body.push_str("level");
        push_arg(&mut body, &entry.level);
        body.push('\n');
        body.push_str("message");
        push_arg(&mut body, &entry.message);
        body.push('\n');
        body.push_str("request_id");
        push_arg(&mut body, &entry.request_id);
        body.push('\n');
        body.push_str(&encode_metadata(&entry.metadata));
        push_block(&mut entries, "entry", &body);
    }
    push_block(&mut out, "entries", &entries);
    out
}

fn encode_profile(data: &ProfileDataset) -> String {
    let mut out = String::new();
    out.push_str("version");
    push_int(&mut out, data.version);
    out.push('\n');
    out.push_str("domain");
    push_arg(&mut out, &data.domain);
    out.push('\n');
    out.push_str("tier");
    push_arg(&mut out, &data.tier);
    out.push('\n');
    let mut profiles = String::new();
    for profile in &data.profiles {
        let mut body = String::new();
        body.push_str("id");
        push_arg(&mut body, &profile.id);
        body.push('\n');
        body.push_str("name");
        push_arg(&mut body, &profile.name);
        body.push('\n');
        body.push_str("email");
        push_arg(&mut body, &profile.email);
        body.push('\n');
        body.push_str("active");
        push_bool(&mut body, profile.active);
        body.push('\n');
        let mut tags = String::new();
        for tag in &profile.tags {
            let mut tag_body = String::new();
            tag_body.push_str("value");
            push_arg(&mut tag_body, tag);
            tag_body.push('\n');
            push_block(&mut tags, "tag", &tag_body);
        }
        push_block(&mut body, "tags", &tags);
        let mut prefs = String::new();
        prefs.push_str("locale");
        push_arg(&mut prefs, &profile.preferences.locale);
        prefs.push('\n');
        prefs.push_str("newsletter");
        push_bool(&mut prefs, profile.preferences.newsletter);
        prefs.push('\n');
        prefs.push_str("theme");
        push_arg(&mut prefs, &profile.preferences.theme);
        prefs.push('\n');
        push_block(&mut body, "preferences", &prefs);
        let mut address = String::new();
        address.push_str("city");
        push_arg(&mut address, &profile.address.city);
        address.push('\n');
        address.push_str("postal_code");
        push_arg(&mut address, &profile.address.postal_code);
        address.push('\n');
        address.push_str("country");
        push_arg(&mut address, &profile.address.country);
        address.push('\n');
        push_block(&mut body, "address", &address);
        push_block(&mut profiles, "profile", &body);
    }
    push_block(&mut out, "profiles", &profiles);
    out
}

fn encode_mesh(data: &MeshDataset) -> String {
    let mut out = String::new();
    out.push_str("version");
    push_int(&mut out, data.version);
    out.push('\n');
    out.push_str("domain");
    push_arg(&mut out, &data.domain);
    out.push('\n');
    out.push_str("tier");
    push_arg(&mut out, &data.tier);
    out.push('\n');
    out.push_str("name");
    push_arg(&mut out, &data.name);
    out.push('\n');
    let mut vertices = String::new();
    for vertex in &data.vertices {
        let mut body = String::new();
        for (key, value) in [
            ("x", vertex.x.to_string()),
            ("y", vertex.y.to_string()),
            ("z", vertex.z.to_string()),
            ("nx", vertex.nx.to_string()),
            ("ny", vertex.ny.to_string()),
            ("nz", vertex.nz.to_string()),
        ] {
            body.push_str(key);
            push_arg(&mut body, &value);
            body.push('\n');
        }
        push_block(&mut vertices, "vertex", &body);
    }
    push_block(&mut out, "vertices", &vertices);
    let mut indices = String::new();
    for index in &data.indices {
        let mut body = String::new();
        body.push_str("value");
        push_int(&mut body, *index);
        body.push('\n');
        push_block(&mut indices, "index", &body);
    }
    push_block(&mut out, "indices", &indices);
    out
}

fn encode_catalog(data: &CatalogDataset) -> String {
    let mut out = String::new();
    out.push_str("version");
    push_int(&mut out, data.version);
    out.push('\n');
    out.push_str("domain");
    push_arg(&mut out, &data.domain);
    out.push('\n');
    out.push_str("tier");
    push_arg(&mut out, &data.tier);
    out.push('\n');
    let mut products = String::new();
    for product in &data.products {
        let mut body = String::new();
        body.push_str("sku");
        push_arg(&mut body, &product.sku);
        body.push('\n');
        body.push_str("name");
        push_arg(&mut body, &product.name);
        body.push('\n');
        body.push_str("price_cents");
        push_int(&mut body, product.price_cents);
        body.push('\n');
        body.push_str("currency");
        push_arg(&mut body, &product.currency);
        body.push('\n');
        body.push_str("in_stock");
        push_bool(&mut body, product.in_stock);
        body.push('\n');
        let mut tags = String::new();
        for tag in &product.tags {
            let mut tag_body = String::new();
            tag_body.push_str("value");
            push_arg(&mut tag_body, tag);
            tag_body.push('\n');
            push_block(&mut tags, "tag", &tag_body);
        }
        push_block(&mut body, "tags", &tags);
        if !product.attributes.is_empty() {
            let mut attrs = String::new();
            for (key, value) in &product.attributes {
                attrs.push_str(key);
                push_arg(&mut attrs, value);
                attrs.push('\n');
            }
            push_block(&mut body, "attributes", &attrs);
        }
        push_block(&mut products, "product", &body);
    }
    push_block(&mut out, "products", &products);
    out
}

#[derive(Debug)]
struct KdlNode {
    name: String,
    args: Vec<String>,
    children: Vec<KdlNode>,
}

fn parse_value(token: &str) -> String {
    if token.starts_with('"') && token.ends_with('"') {
        token[1..token.len() - 1]
            .replace("\\\"", "\"")
            .replace("\\\\", "\\")
    } else {
        token.to_string()
    }
}

fn parse_nodes(lines: &[&str], index: &mut usize, indent: usize) -> Vec<KdlNode> {
    let mut nodes = Vec::new();
    while *index < lines.len() {
        let raw = lines[*index];
        if raw.trim().is_empty() {
            *index += 1;
            continue;
        }
        let line_indent = raw.chars().take_while(|ch| ch.is_whitespace()).count();
        if line_indent < indent {
            break;
        }
        if line_indent > indent {
            panic!("unexpected indent");
        }
        let trimmed = raw.trim();
        if trimmed == "}" {
            *index += 1;
            break;
        }
        let (head, has_block) = if let Some(pos) = trimmed.find('{') {
            (trimmed[..pos].trim(), true)
        } else {
            (trimmed, false)
        };
        let mut parts = head.split_whitespace();
        let name = parts.next().expect("node name").to_string();
        let args = parts.map(parse_value).collect();
        *index += 1;
        let children = if has_block {
            parse_nodes(lines, index, indent + 2)
        } else {
            Vec::new()
        };
        nodes.push(KdlNode {
            name,
            args,
            children,
        });
    }
    nodes
}

fn parse_document(text: &str) -> Vec<KdlNode> {
    let lines: Vec<&str> = text.lines().collect();
    let mut index = 0;
    parse_nodes(&lines, &mut index, 0)
}

fn child<'a>(nodes: &'a [KdlNode], name: &str) -> &'a KdlNode {
    nodes
        .iter()
        .find(|node| node.name == name)
        .unwrap_or_else(|| panic!("missing node {name}"))
}

fn child_opt<'a>(nodes: &'a [KdlNode], name: &str) -> Option<&'a KdlNode> {
    nodes.iter().find(|node| node.name == name)
}

fn children<'a>(nodes: &'a [KdlNode], name: &str) -> Vec<&'a KdlNode> {
    nodes.iter().filter(|node| node.name == name).collect()
}

fn arg_string(node: &KdlNode) -> String {
    node.args.first().cloned().unwrap_or_default()
}

fn arg_u32(node: &KdlNode) -> u32 {
    arg_string(node).parse().expect("u32")
}

fn arg_u16(node: &KdlNode) -> u16 {
    arg_u32(node) as u16
}

fn arg_bool(node: &KdlNode) -> bool {
    matches!(arg_string(node).as_str(), "true" | "1")
}

fn arg_f32(node: &KdlNode) -> f32 {
    arg_string(node).parse().expect("f32")
}

fn decode_logs(text: &str) -> LogDataset {
    let doc = parse_document(text);
    let entries_node = child(&doc, "entries");
    let entries = children(&entries_node.children, "entry")
        .into_iter()
        .map(|entry| {
            let metadata = child(&entry.children, "metadata");
            LogEntry {
                timestamp: arg_string(child(&entry.children, "timestamp")),
                level: arg_string(child(&entry.children, "level")),
                message: arg_string(child(&entry.children, "message")),
                request_id: arg_string(child(&entry.children, "request_id")),
                metadata: LogMetadata {
                    status: arg_u16(child(&metadata.children, "status")),
                    duration_ms: arg_u32(child(&metadata.children, "duration_ms")),
                    bytes_sent: arg_u32(child(&metadata.children, "bytes_sent")),
                    user_agent: arg_string(child(&metadata.children, "user_agent")),
                    remote_addr: arg_string(child(&metadata.children, "remote_addr")),
                },
            }
        })
        .collect();
    LogDataset {
        version: arg_u32(child(&doc, "version")),
        domain: arg_string(child(&doc, "domain")),
        tier: arg_string(child(&doc, "tier")),
        entries,
    }
}

fn decode_profile(text: &str) -> ProfileDataset {
    let doc = parse_document(text);
    let profiles_node = child(&doc, "profiles");
    let profiles = children(&profiles_node.children, "profile")
        .into_iter()
        .map(|profile| {
            let prefs = child(&profile.children, "preferences");
            let address = child(&profile.children, "address");
            let tags_node = child(&profile.children, "tags");
            let tags = children(&tags_node.children, "tag")
                .into_iter()
                .map(|tag| arg_string(child(&tag.children, "value")))
                .collect();
            Profile {
                id: arg_string(child(&profile.children, "id")),
                name: arg_string(child(&profile.children, "name")),
                email: arg_string(child(&profile.children, "email")),
                active: arg_bool(child(&profile.children, "active")),
                tags,
                preferences: ProfilePreferences {
                    locale: arg_string(child(&prefs.children, "locale")),
                    newsletter: arg_bool(child(&prefs.children, "newsletter")),
                    theme: arg_string(child(&prefs.children, "theme")),
                },
                address: ProfileAddress {
                    city: arg_string(child(&address.children, "city")),
                    postal_code: arg_string(child(&address.children, "postal_code")),
                    country: arg_string(child(&address.children, "country")),
                },
            }
        })
        .collect();
    ProfileDataset {
        version: arg_u32(child(&doc, "version")),
        domain: arg_string(child(&doc, "domain")),
        tier: arg_string(child(&doc, "tier")),
        profiles,
    }
}

fn decode_mesh(text: &str) -> MeshDataset {
    let doc = parse_document(text);
    let vertices_node = child(&doc, "vertices");
    let vertices = children(&vertices_node.children, "vertex")
        .into_iter()
        .map(|vertex| Vertex {
            x: arg_f32(child(&vertex.children, "x")),
            y: arg_f32(child(&vertex.children, "y")),
            z: arg_f32(child(&vertex.children, "z")),
            nx: arg_f32(child(&vertex.children, "nx")),
            ny: arg_f32(child(&vertex.children, "ny")),
            nz: arg_f32(child(&vertex.children, "nz")),
        })
        .collect();
    let indices_node = child(&doc, "indices");
    let indices = children(&indices_node.children, "index")
        .into_iter()
        .map(|index| arg_u32(child(&index.children, "value")))
        .collect();
    MeshDataset {
        version: arg_u32(child(&doc, "version")),
        domain: arg_string(child(&doc, "domain")),
        tier: arg_string(child(&doc, "tier")),
        name: arg_string(child(&doc, "name")),
        vertices,
        indices,
    }
}

fn decode_catalog(text: &str) -> CatalogDataset {
    let doc = parse_document(text);
    let products_node = child(&doc, "products");
    let products = children(&products_node.children, "product")
        .into_iter()
        .map(|product| {
            let tags_node = child(&product.children, "tags");
            let tags = children(&tags_node.children, "tag")
                .into_iter()
                .map(|tag| arg_string(child(&tag.children, "value")))
                .collect();
            let mut attributes = std::collections::BTreeMap::new();
            if let Some(attrs) = child_opt(&product.children, "attributes") {
                for child_node in &attrs.children {
                    attributes.insert(child_node.name.clone(), arg_string(child_node));
                }
            }
            Product {
                sku: arg_string(child(&product.children, "sku")),
                name: arg_string(child(&product.children, "name")),
                price_cents: arg_u32(child(&product.children, "price_cents")),
                currency: arg_string(child(&product.children, "currency")),
                in_stock: arg_bool(child(&product.children, "in_stock")),
                tags,
                attributes,
            }
        })
        .collect();
    CatalogDataset {
        version: arg_u32(child(&doc, "version")),
        domain: arg_string(child(&doc, "domain")),
        tier: arg_string(child(&doc, "tier")),
        products,
    }
}
