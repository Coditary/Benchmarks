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
    let text = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(decode_logs(text)),
        "profile" => DecodedDataset::Profile(decode_profile(text)),
        "mesh" => DecodedDataset::Mesh(decode_mesh(text)),
        "catalog" => DecodedDataset::Catalog(decode_catalog(text)),
        "ast" => DecodedDataset::Ast(decode_ast(text)),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn quote(value: &str) -> String {
    format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
}

fn push_scalar(out: &mut String, key: &str, value: &str, quoted: bool) {
    out.push_str(key);
    out.push(' ');
    if quoted {
        out.push_str(&quote(value));
    } else {
        out.push_str(value);
    }
    out.push(';');
    out.push('\n');
}

fn push_object(out: &mut String, key: &str, body: &str) {
    out.push_str(key);
    out.push_str(" {\n");
    out.push_str(body);
    out.push_str("}\n");
}

fn push_array(out: &mut String, key: &str, items: &[String]) {
    out.push_str(key);
    out.push_str(" [\n");
    for item in items {
        out.push_str("  {\n");
        out.push_str(item);
        out.push_str("  }\n");
    }
    out.push_str("]\n");
}

fn encode_metadata(metadata: &LogMetadata) -> String {
    let mut inner = String::new();
    push_scalar(&mut inner, "status", &metadata.status.to_string(), false);
    push_scalar(&mut inner, "duration_ms", &metadata.duration_ms.to_string(), false);
    push_scalar(&mut inner, "bytes_sent", &metadata.bytes_sent.to_string(), false);
    push_scalar(&mut inner, "user_agent", &metadata.user_agent, true);
    push_scalar(&mut inner, "remote_addr", &metadata.remote_addr, true);
    inner
}

fn encode_logs(data: &LogDataset) -> String {
    let mut out = String::new();
    push_scalar(&mut out, "version", &data.version.to_string(), false);
    push_scalar(&mut out, "domain", &data.domain, true);
    push_scalar(&mut out, "tier", &data.tier, true);
    let mut entries = Vec::new();
    for entry in &data.entries {
        let mut body = String::new();
        push_scalar(&mut body, "timestamp", &entry.timestamp, true);
        push_scalar(&mut body, "level", &entry.level, true);
        push_scalar(&mut body, "message", &entry.message, true);
        push_scalar(&mut body, "request_id", &entry.request_id, true);
        let metadata = encode_metadata(&entry.metadata);
        push_object(&mut body, "metadata", &metadata);
        entries.push(body);
    }
    push_array(&mut out, "entries", &entries);
    out
}

fn encode_profile(data: &ProfileDataset) -> String {
    let mut out = String::new();
    push_scalar(&mut out, "version", &data.version.to_string(), false);
    push_scalar(&mut out, "domain", &data.domain, true);
    push_scalar(&mut out, "tier", &data.tier, true);
    let mut profiles = Vec::new();
    for profile in &data.profiles {
        let mut body = String::new();
        push_scalar(&mut body, "id", &profile.id, true);
        push_scalar(&mut body, "name", &profile.name, true);
        push_scalar(&mut body, "email", &profile.email, true);
        push_scalar(
            &mut body,
            "active",
            if profile.active { "true" } else { "false" },
            false,
        );
        let tags: Vec<String> = profile
            .tags
            .iter()
            .map(|tag| {
                let mut tag_body = String::new();
                push_scalar(&mut tag_body, "value", tag, true);
                tag_body
            })
            .collect();
        push_array(&mut body, "tags", &tags);
        let mut prefs = String::new();
        push_scalar(&mut prefs, "locale", &profile.preferences.locale, true);
        push_scalar(
            &mut prefs,
            "newsletter",
            if profile.preferences.newsletter {
                "true"
            } else {
                "false"
            },
            false,
        );
        push_scalar(&mut prefs, "theme", &profile.preferences.theme, true);
        push_object(&mut body, "preferences", &prefs);
        let mut address = String::new();
        push_scalar(&mut address, "city", &profile.address.city, true);
        push_scalar(&mut address, "postal_code", &profile.address.postal_code, true);
        push_scalar(&mut address, "country", &profile.address.country, true);
        push_object(&mut body, "address", &address);
        profiles.push(body);
    }
    push_array(&mut out, "profiles", &profiles);
    out
}

fn encode_mesh(data: &MeshDataset) -> String {
    let mut out = String::new();
    push_scalar(&mut out, "version", &data.version.to_string(), false);
    push_scalar(&mut out, "domain", &data.domain, true);
    push_scalar(&mut out, "tier", &data.tier, true);
    push_scalar(&mut out, "name", &data.name, true);
    let vertices: Vec<String> = data
        .vertices
        .iter()
        .map(|vertex| {
            let mut body = String::new();
            for (key, value) in [
                ("x", vertex.x.to_string()),
                ("y", vertex.y.to_string()),
                ("z", vertex.z.to_string()),
                ("nx", vertex.nx.to_string()),
                ("ny", vertex.ny.to_string()),
                ("nz", vertex.nz.to_string()),
            ] {
                push_scalar(&mut body, key, &value, false);
            }
            body
        })
        .collect();
    push_array(&mut out, "vertices", &vertices);
    let indices: Vec<String> = data
        .indices
        .iter()
        .map(|index| {
            let mut body = String::new();
            push_scalar(&mut body, "value", &index.to_string(), false);
            body
        })
        .collect();
    push_array(&mut out, "indices", &indices);
    out
}

fn encode_catalog(data: &CatalogDataset) -> String {
    let mut out = String::new();
    push_scalar(&mut out, "version", &data.version.to_string(), false);
    push_scalar(&mut out, "domain", &data.domain, true);
    push_scalar(&mut out, "tier", &data.tier, true);
    let mut products = Vec::new();
    for product in &data.products {
        let mut body = String::new();
        push_scalar(&mut body, "sku", &product.sku, true);
        push_scalar(&mut body, "name", &product.name, true);
        push_scalar(&mut body, "price_cents", &product.price_cents.to_string(), false);
        push_scalar(&mut body, "currency", &product.currency, true);
        push_scalar(
            &mut body,
            "in_stock",
            if product.in_stock { "true" } else { "false" },
            false,
        );
        let tags: Vec<String> = product
            .tags
            .iter()
            .map(|tag| {
                let mut tag_body = String::new();
                push_scalar(&mut tag_body, "value", tag, true);
                tag_body
            })
            .collect();
        push_array(&mut body, "tags", &tags);
        if !product.attributes.is_empty() {
            let mut attrs = String::new();
            for (key, value) in &product.attributes {
                push_scalar(&mut attrs, key, value, true);
            }
            push_object(&mut body, "attributes", &attrs);
        }
        products.push(body);
    }
    push_array(&mut out, "products", &products);
    out
}

fn encode_ast_span(span: &AstSpan) -> String {
    let mut inner = String::new();
    push_scalar(&mut inner, "line", &span.line.to_string(), false);
    push_scalar(&mut inner, "column", &span.column.to_string(), false);
    inner
}

fn encode_ast_node(node: &AstNode) -> String {
    let mut body = String::new();
    push_scalar(&mut body, "node_type", &node.node_type, true);
    push_scalar(&mut body, "id", &node.id.to_string(), false);
    push_scalar(&mut body, "name", &node.name, true);
    push_object(&mut body, "span", &encode_ast_span(&node.span));
    if let Some(value) = &node.value {
        push_scalar(&mut body, "value", value, true);
    }
    if !node.children.is_empty() {
        let children: Vec<String> = node.children.iter().map(|child| encode_ast_node(child)).collect();
        push_array(&mut body, "children", &children);
    }
    body
}

fn encode_ast(data: &AstDataset) -> String {
    let mut out = String::new();
    push_scalar(&mut out, "version", &data.version.to_string(), false);
    push_scalar(&mut out, "domain", &data.domain, true);
    push_scalar(&mut out, "tier", &data.tier, true);
    push_scalar(&mut out, "max_depth", &data.max_depth.to_string(), false);
    let trees: Vec<String> = data.trees.iter().map(encode_ast_node).collect();
    push_array(&mut out, "trees", &trees);
    out
}

#[derive(Debug)]
enum UclValue {
    Scalar(String),
    Object(Vec<UclNode>),
    Array(Vec<Vec<UclNode>>),
}

#[derive(Debug)]
struct UclNode {
    name: String,
    value: UclValue,
}

struct Parser<'a> {
    input: &'a str,
    pos: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Self { input, pos: 0 }
    }

    fn peek(&self) -> Option<char> {
        self.input[self.pos..].chars().next()
    }

    fn bump(&mut self) -> Option<char> {
        let ch = self.peek()?;
        self.pos += ch.len_utf8();
        Some(ch)
    }

    fn skip_ws(&mut self) {
        while let Some(ch) = self.peek() {
            if ch.is_whitespace() {
                self.bump();
            } else {
                break;
            }
        }
    }

    fn expect(&mut self, expected: char) {
        self.skip_ws();
        let ch = self.bump().unwrap_or_else(|| panic!("expected '{expected}'"));
        if ch != expected {
            panic!("expected '{expected}', found '{ch}'");
        }
    }

    fn parse_identifier(&mut self) -> String {
        self.skip_ws();
        let start = self.pos;
        while let Some(ch) = self.peek() {
            if ch.is_alphanumeric() || ch == '_' || ch == '-' {
                self.bump();
            } else {
                break;
            }
        }
        let name = &self.input[start..self.pos];
        assert!(!name.is_empty(), "expected identifier");
        name.to_string()
    }

    fn parse_quoted_string(&mut self) -> String {
        self.expect('"');
        let mut out = String::new();
        while let Some(ch) = self.peek() {
            if ch == '"' {
                self.bump();
                break;
            }
            if ch == '\\' {
                self.bump();
                let escaped = self.bump().expect("truncated escape");
                match escaped {
                    '"' => out.push('"'),
                    '\\' => out.push('\\'),
                    other => {
                        out.push('\\');
                        out.push(other);
                    }
                }
            } else {
                out.push(ch);
                self.bump();
            }
        }
        out
    }

    fn parse_scalar_token(&mut self) -> String {
        self.skip_ws();
        let start = self.pos;
        while let Some(ch) = self.peek() {
            if ch.is_whitespace() || ch == ';' || ch == '}' || ch == ']' {
                break;
            }
            self.bump();
        }
        let token = &self.input[start..self.pos];
        assert!(!token.is_empty(), "expected scalar token");
        token.to_string()
    }

    fn parse_value(&mut self) -> UclValue {
        self.skip_ws();
        match self.peek() {
            Some('"') => UclValue::Scalar(self.parse_quoted_string()),
            Some('{') => {
                self.bump();
                UclValue::Object(self.parse_object_fields())
            }
            Some('[') => {
                self.bump();
                UclValue::Array(self.parse_array_objects())
            }
            _ => UclValue::Scalar(self.parse_scalar_token()),
        }
    }

    fn parse_field(&mut self) -> UclNode {
        let name = self.parse_identifier();
        let value = self.parse_value();
        self.skip_ws();
        if self.peek() == Some(';') {
            self.bump();
        }
        UclNode { name, value }
    }

    fn parse_object_fields(&mut self) -> Vec<UclNode> {
        let mut fields = Vec::new();
        loop {
            self.skip_ws();
            if self.peek() == Some('}') {
                self.bump();
                break;
            }
            fields.push(self.parse_field());
        }
        fields
    }

    fn parse_array_objects(&mut self) -> Vec<Vec<UclNode>> {
        let mut items = Vec::new();
        loop {
            self.skip_ws();
            if self.peek() == Some(']') {
                self.bump();
                break;
            }
            self.expect('{');
            items.push(self.parse_object_fields());
        }
        items
    }

    fn parse_document(&mut self) -> Vec<UclNode> {
        let mut nodes = Vec::new();
        loop {
            self.skip_ws();
            if self.pos >= self.input.len() {
                break;
            }
            nodes.push(self.parse_field());
        }
        nodes
    }
}

fn parse_document(text: &str) -> Vec<UclNode> {
    Parser::new(text).parse_document()
}

fn child<'a>(nodes: &'a [UclNode], name: &str) -> &'a UclNode {
    nodes
        .iter()
        .find(|node| node.name == name)
        .unwrap_or_else(|| panic!("missing field {name}"))
}

fn child_opt<'a>(nodes: &'a [UclNode], name: &str) -> Option<&'a UclNode> {
    nodes.iter().find(|node| node.name == name)
}

fn scalar_string(node: &UclNode) -> String {
    match &node.value {
        UclValue::Scalar(value) => value.clone(),
        _ => panic!("expected scalar for {}", node.name),
    }
}

fn object_fields(node: &UclNode) -> &[UclNode] {
    match &node.value {
        UclValue::Object(fields) => fields,
        _ => panic!("expected object for {}", node.name),
    }
}

fn array_objects(node: &UclNode) -> &[Vec<UclNode>] {
    match &node.value {
        UclValue::Array(items) => items,
        _ => panic!("expected array for {}", node.name),
    }
}

fn arg_u32(node: &UclNode) -> u32 {
    scalar_string(node).parse().expect("u32")
}

fn arg_u16(node: &UclNode) -> u16 {
    arg_u32(node) as u16
}

fn arg_bool(node: &UclNode) -> bool {
    matches!(scalar_string(node).as_str(), "true" | "1")
}

fn arg_f32(node: &UclNode) -> f32 {
    scalar_string(node).parse().expect("f32")
}

fn decode_logs(text: &str) -> LogDataset {
    let doc = parse_document(text);
    let entries = array_objects(child(&doc, "entries"))
        .iter()
        .map(|entry| {
            let metadata = child(entry, "metadata");
            LogEntry {
                timestamp: scalar_string(child(entry, "timestamp")),
                level: scalar_string(child(entry, "level")),
                message: scalar_string(child(entry, "message")),
                request_id: scalar_string(child(entry, "request_id")),
                metadata: LogMetadata {
                    status: arg_u16(child(object_fields(metadata), "status")),
                    duration_ms: arg_u32(child(object_fields(metadata), "duration_ms")),
                    bytes_sent: arg_u32(child(object_fields(metadata), "bytes_sent")),
                    user_agent: scalar_string(child(object_fields(metadata), "user_agent")),
                    remote_addr: scalar_string(child(object_fields(metadata), "remote_addr")),
                },
            }
        })
        .collect();
    LogDataset {
        version: arg_u32(child(&doc, "version")),
        domain: scalar_string(child(&doc, "domain")),
        tier: scalar_string(child(&doc, "tier")),
        entries,
    }
}

fn decode_profile(text: &str) -> ProfileDataset {
    let doc = parse_document(text);
    let profiles = array_objects(child(&doc, "profiles"))
        .iter()
        .map(|profile| {
            let prefs = child(profile, "preferences");
            let address = child(profile, "address");
            let tags = array_objects(child(profile, "tags"))
                .iter()
                .map(|tag| scalar_string(child(tag, "value")))
                .collect();
            Profile {
                id: scalar_string(child(profile, "id")),
                name: scalar_string(child(profile, "name")),
                email: scalar_string(child(profile, "email")),
                active: arg_bool(child(profile, "active")),
                tags,
                preferences: ProfilePreferences {
                    locale: scalar_string(child(object_fields(prefs), "locale")),
                    newsletter: arg_bool(child(object_fields(prefs), "newsletter")),
                    theme: scalar_string(child(object_fields(prefs), "theme")),
                },
                address: ProfileAddress {
                    city: scalar_string(child(object_fields(address), "city")),
                    postal_code: scalar_string(child(object_fields(address), "postal_code")),
                    country: scalar_string(child(object_fields(address), "country")),
                },
            }
        })
        .collect();
    ProfileDataset {
        version: arg_u32(child(&doc, "version")),
        domain: scalar_string(child(&doc, "domain")),
        tier: scalar_string(child(&doc, "tier")),
        profiles,
    }
}

fn decode_mesh(text: &str) -> MeshDataset {
    let doc = parse_document(text);
    let vertices = array_objects(child(&doc, "vertices"))
        .iter()
        .map(|vertex| Vertex {
            x: arg_f32(child(vertex, "x")),
            y: arg_f32(child(vertex, "y")),
            z: arg_f32(child(vertex, "z")),
            nx: arg_f32(child(vertex, "nx")),
            ny: arg_f32(child(vertex, "ny")),
            nz: arg_f32(child(vertex, "nz")),
        })
        .collect();
    let indices = array_objects(child(&doc, "indices"))
        .iter()
        .map(|index| arg_u32(child(index, "value")))
        .collect();
    MeshDataset {
        version: arg_u32(child(&doc, "version")),
        domain: scalar_string(child(&doc, "domain")),
        tier: scalar_string(child(&doc, "tier")),
        name: scalar_string(child(&doc, "name")),
        vertices,
        indices,
    }
}

fn decode_catalog(text: &str) -> CatalogDataset {
    let doc = parse_document(text);
    let products = array_objects(child(&doc, "products"))
        .iter()
        .map(|product| {
            let tags = array_objects(child(product, "tags"))
                .iter()
                .map(|tag| scalar_string(child(tag, "value")))
                .collect();
            let mut attributes = std::collections::BTreeMap::new();
            if let Some(attrs) = child_opt(product, "attributes") {
                for field in object_fields(attrs) {
                    attributes.insert(field.name.clone(), scalar_string(field));
                }
            }
            Product {
                sku: scalar_string(child(product, "sku")),
                name: scalar_string(child(product, "name")),
                price_cents: arg_u32(child(product, "price_cents")),
                currency: scalar_string(child(product, "currency")),
                in_stock: arg_bool(child(product, "in_stock")),
                tags,
                attributes,
            }
        })
        .collect();
    CatalogDataset {
        version: arg_u32(child(&doc, "version")),
        domain: scalar_string(child(&doc, "domain")),
        tier: scalar_string(child(&doc, "tier")),
        products,
    }
}

fn arg_u64(node: &UclNode) -> u64 {
    scalar_string(node).parse().expect("u64")
}

fn decode_ast_node(fields: &[UclNode]) -> AstNode {
    let children = child_opt(fields, "children")
        .map(|children_node| {
            array_objects(children_node)
                .iter()
                .map(|child| Box::new(decode_ast_node(child)))
                .collect()
        })
        .unwrap_or_default();
    AstNode {
        node_type: scalar_string(child(fields, "node_type")),
        id: arg_u64(child(fields, "id")),
        name: scalar_string(child(fields, "name")),
        span: AstSpan {
            line: arg_u32(child(object_fields(child(fields, "span")), "line")),
            column: arg_u32(child(object_fields(child(fields, "span")), "column")),
        },
        value: child_opt(fields, "value").map(scalar_string),
        children,
    }
}

fn decode_ast(text: &str) -> AstDataset {
    let doc = parse_document(text);
    let trees = array_objects(child(&doc, "trees"))
        .iter()
        .map(|tree| decode_ast_node(tree))
        .collect();
    AstDataset {
        version: arg_u32(child(&doc, "version")),
        domain: scalar_string(child(&doc, "domain")),
        tier: scalar_string(child(&doc, "tier")),
        max_depth: arg_u32(child(&doc, "max_depth")),
        trees,
    }
}
