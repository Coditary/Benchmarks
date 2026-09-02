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

fn escape_ini(value: &str) -> String {
    if value.contains(['\n', '\r', '"', '\\']) {
        format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
    } else {
        value.to_string()
    }
}

fn write_section_header(out: &mut String, section: &str) {
    out.push('[');
    out.push_str(section);
    out.push_str("]\n");
}

fn write_kv(out: &mut String, key: &str, value: &str) {
    out.push_str(key);
    out.push('=');
    out.push_str(&escape_ini(value));
    out.push('\n');
}

fn write_kv_u64(out: &mut String, key: &str, value: u64) {
    out.push_str(key);
    out.push('=');
    out.push_str(&value.to_string());
    out.push('\n');
}

fn write_kv_bool(out: &mut String, key: &str, value: bool) {
    write_kv(out, key, if value { "true" } else { "false" });
}

fn encode_logs(data: &LogDataset) -> String {
    let mut out = String::new();
    write_section_header(&mut out, "dataset");
    write_kv_u64(&mut out, "version", data.version as u64);
    write_kv(&mut out, "domain", &data.domain);
    write_kv(&mut out, "tier", &data.tier);
    out.push('\n');
    for (index, entry) in data.entries.iter().enumerate() {
        let prefix = format!("entry.{index}");
        write_section_header(&mut out, &prefix);
        write_kv(&mut out, "timestamp", &entry.timestamp);
        write_kv(&mut out, "level", &entry.level);
        write_kv(&mut out, "message", &entry.message);
        write_kv(&mut out, "request_id", &entry.request_id);
        out.push('\n');
        let meta = format!("{prefix}.metadata");
        write_section_header(&mut out, &meta);
        write_kv_u64(&mut out, "status", entry.metadata.status as u64);
        write_kv_u64(&mut out, "duration_ms", entry.metadata.duration_ms as u64);
        write_kv_u64(&mut out, "bytes_sent", entry.metadata.bytes_sent as u64);
        write_kv(&mut out, "user_agent", &entry.metadata.user_agent);
        write_kv(&mut out, "remote_addr", &entry.metadata.remote_addr);
        out.push('\n');
    }
    out
}

fn encode_profile(data: &ProfileDataset) -> String {
    let mut out = String::new();
    write_section_header(&mut out, "dataset");
    write_kv_u64(&mut out, "version", data.version as u64);
    write_kv(&mut out, "domain", &data.domain);
    write_kv(&mut out, "tier", &data.tier);
    out.push('\n');
    for (index, profile) in data.profiles.iter().enumerate() {
        let prefix = format!("profile.{index}");
        write_section_header(&mut out, &prefix);
        write_kv(&mut out, "id", &profile.id);
        write_kv(&mut out, "name", &profile.name);
        write_kv(&mut out, "email", &profile.email);
        write_kv_bool(&mut out, "active", profile.active);
        write_kv(&mut out, "tags", &profile.tags.join(","));
        out.push('\n');
        let prefs = format!("{prefix}.preferences");
        write_section_header(&mut out, &prefs);
        write_kv(&mut out, "locale", &profile.preferences.locale);
        write_kv_bool(&mut out, "newsletter", profile.preferences.newsletter);
        write_kv(&mut out, "theme", &profile.preferences.theme);
        out.push('\n');
        let address = format!("{prefix}.address");
        write_section_header(&mut out, &address);
        write_kv(&mut out, "city", &profile.address.city);
        write_kv(&mut out, "postal_code", &profile.address.postal_code);
        write_kv(&mut out, "country", &profile.address.country);
        out.push('\n');
    }
    out
}

fn encode_mesh(data: &MeshDataset) -> String {
    let mut out = String::new();
    write_section_header(&mut out, "dataset");
    write_kv_u64(&mut out, "version", data.version as u64);
    write_kv(&mut out, "domain", &data.domain);
    write_kv(&mut out, "tier", &data.tier);
    write_kv(&mut out, "name", &data.name);
    out.push('\n');
    for (index, vertex) in data.vertices.iter().enumerate() {
        let section = format!("vertex.{index}");
        write_section_header(&mut out, &section);
        write_kv(&mut out, "x", &vertex.x.to_string());
        write_kv(&mut out, "y", &vertex.y.to_string());
        write_kv(&mut out, "z", &vertex.z.to_string());
        write_kv(&mut out, "nx", &vertex.nx.to_string());
        write_kv(&mut out, "ny", &vertex.ny.to_string());
        write_kv(&mut out, "nz", &vertex.nz.to_string());
        out.push('\n');
    }
    write_section_header(&mut out, "indices");
    for (index, value) in data.indices.iter().enumerate() {
        write_kv_u64(&mut out, &index.to_string(), *value as u64);
    }
    out.push('\n');
    out
}

fn encode_catalog(data: &CatalogDataset) -> String {
    let mut out = String::new();
    write_section_header(&mut out, "dataset");
    write_kv_u64(&mut out, "version", data.version as u64);
    write_kv(&mut out, "domain", &data.domain);
    write_kv(&mut out, "tier", &data.tier);
    out.push('\n');
    for (index, product) in data.products.iter().enumerate() {
        let prefix = format!("product.{index}");
        write_section_header(&mut out, &prefix);
        write_kv(&mut out, "sku", &product.sku);
        write_kv(&mut out, "name", &product.name);
        write_kv_u64(&mut out, "price_cents", product.price_cents as u64);
        write_kv(&mut out, "currency", &product.currency);
        write_kv_bool(&mut out, "in_stock", product.in_stock);
        write_kv(&mut out, "tags", &product.tags.join(","));
        out.push('\n');
        if !product.attributes.is_empty() {
            let attrs = format!("{prefix}.attributes");
            write_section_header(&mut out, &attrs);
            for (key, value) in &product.attributes {
                write_kv(&mut out, key, value);
            }
            out.push('\n');
        }
    }
    out
}

fn parse_ini(text: &str) -> std::collections::HashMap<String, std::collections::HashMap<String, String>> {
    let mut sections: std::collections::HashMap<String, std::collections::HashMap<String, String>> =
        std::collections::HashMap::new();
    let mut current = String::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with(';') || line.starts_with('#') {
            continue;
        }
        if let Some(inner) = line.strip_prefix('[').and_then(|rest| rest.strip_suffix(']')) {
            current = inner.to_string();
            sections.entry(current.clone()).or_default();
            continue;
        }
        if let Some((key, value)) = line.split_once('=') {
            sections
                .entry(current.clone())
                .or_default()
                .insert(key.trim().to_string(), value.trim().trim_matches('"').to_string());
        }
    }
    sections
}

fn section<'a>(
    sections: &'a std::collections::HashMap<String, std::collections::HashMap<String, String>>,
    name: &str,
) -> &'a std::collections::HashMap<String, String> {
    sections.get(name).unwrap_or_else(|| panic!("missing section [{name}]"))
}

fn get_str(map: &std::collections::HashMap<String, String>, key: &str) -> String {
    map.get(key)
        .cloned()
        .unwrap_or_else(|| panic!("missing key {key}"))
}

fn get_u32(map: &std::collections::HashMap<String, String>, key: &str) -> u32 {
    get_str(map, key).parse().expect("u32")
}

fn get_u16(map: &std::collections::HashMap<String, String>, key: &str) -> u16 {
    get_str(map, key).parse().expect("u16")
}

fn get_bool(map: &std::collections::HashMap<String, String>, key: &str) -> bool {
    matches!(get_str(map, key).as_str(), "true" | "1" | "yes")
}

fn get_f32(map: &std::collections::HashMap<String, String>, key: &str) -> f32 {
    get_str(map, key).parse().expect("f32")
}

fn decode_logs(text: &str) -> LogDataset {
    let sections = parse_ini(text);
    let dataset = section(&sections, "dataset");
    let version = get_u32(dataset, "version");
    let domain = get_str(dataset, "domain");
    let tier = get_str(dataset, "tier");
    let mut entries = Vec::new();
    let mut index = 0;
    loop {
        let name = format!("entry.{index}");
        if !sections.contains_key(&name) {
            break;
        }
        let entry_map = section(&sections, &name);
        let metadata_map = section(&sections, &format!("{name}.metadata"));
        entries.push(LogEntry {
            timestamp: get_str(entry_map, "timestamp"),
            level: get_str(entry_map, "level"),
            message: get_str(entry_map, "message"),
            request_id: get_str(entry_map, "request_id"),
            metadata: LogMetadata {
                status: get_u16(metadata_map, "status"),
                duration_ms: get_u32(metadata_map, "duration_ms"),
                bytes_sent: get_u32(metadata_map, "bytes_sent"),
                user_agent: get_str(metadata_map, "user_agent"),
                remote_addr: get_str(metadata_map, "remote_addr"),
            },
        });
        index += 1;
    }
    LogDataset {
        version,
        domain,
        tier,
        entries,
    }
}

fn decode_profile(text: &str) -> ProfileDataset {
    let sections = parse_ini(text);
    let dataset = section(&sections, "dataset");
    let mut profiles = Vec::new();
    let mut index = 0;
    loop {
        let name = format!("profile.{index}");
        if !sections.contains_key(&name) {
            break;
        }
        let profile_map = section(&sections, &name);
        let prefs_map = section(&sections, &format!("{name}.preferences"));
        let address_map = section(&sections, &format!("{name}.address"));
        let tags = get_str(profile_map, "tags");
        profiles.push(Profile {
            id: get_str(profile_map, "id"),
            name: get_str(profile_map, "name"),
            email: get_str(profile_map, "email"),
            active: get_bool(profile_map, "active"),
            tags: if tags.is_empty() {
                Vec::new()
            } else {
                tags.split(',').map(str::to_string).collect()
            },
            preferences: ProfilePreferences {
                locale: get_str(prefs_map, "locale"),
                newsletter: get_bool(prefs_map, "newsletter"),
                theme: get_str(prefs_map, "theme"),
            },
            address: ProfileAddress {
                city: get_str(address_map, "city"),
                postal_code: get_str(address_map, "postal_code"),
                country: get_str(address_map, "country"),
            },
        });
        index += 1;
    }
    ProfileDataset {
        version: get_u32(dataset, "version"),
        domain: get_str(dataset, "domain"),
        tier: get_str(dataset, "tier"),
        profiles,
    }
}

fn decode_mesh(text: &str) -> MeshDataset {
    let sections = parse_ini(text);
    let dataset = section(&sections, "dataset");
    let mut vertices = Vec::new();
    let mut index = 0;
    loop {
        let name = format!("vertex.{index}");
        if !sections.contains_key(&name) {
            break;
        }
        let map = section(&sections, &name);
        vertices.push(Vertex {
            x: get_f32(map, "x"),
            y: get_f32(map, "y"),
            z: get_f32(map, "z"),
            nx: get_f32(map, "nx"),
            ny: get_f32(map, "ny"),
            nz: get_f32(map, "nz"),
        });
        index += 1;
    }
    let indices_map = section(&sections, "indices");
    let mut indices: Vec<_> = indices_map
        .iter()
        .map(|(key, value)| (key.parse::<usize>().expect("index key"), value.parse::<u32>().expect("u32")))
        .collect();
    indices.sort_by_key(|(key, _)| *key);
    MeshDataset {
        version: get_u32(dataset, "version"),
        domain: get_str(dataset, "domain"),
        tier: get_str(dataset, "tier"),
        name: get_str(dataset, "name"),
        vertices,
        indices: indices.into_iter().map(|(_, value)| value).collect(),
    }
}

fn decode_catalog(text: &str) -> CatalogDataset {
    let sections = parse_ini(text);
    let dataset = section(&sections, "dataset");
    let mut products = Vec::new();
    let mut index = 0;
    loop {
        let name = format!("product.{index}");
        if !sections.contains_key(&name) {
            break;
        }
        let product_map = section(&sections, &name);
        let attrs_name = format!("{name}.attributes");
        let mut attributes = std::collections::BTreeMap::new();
        if let Some(attrs) = sections.get(&attrs_name) {
            attributes.extend(attrs.clone());
        }
        let tags = get_str(product_map, "tags");
        products.push(Product {
            sku: get_str(product_map, "sku"),
            name: get_str(product_map, "name"),
            price_cents: get_u32(product_map, "price_cents"),
            currency: get_str(product_map, "currency"),
            in_stock: get_bool(product_map, "in_stock"),
            tags: if tags.is_empty() {
                Vec::new()
            } else {
                tags.split(',').map(str::to_string).collect()
            },
            attributes,
        });
        index += 1;
    }
    CatalogDataset {
        version: get_u32(dataset, "version"),
        domain: get_str(dataset, "domain"),
        tier: get_str(dataset, "tier"),
        products,
    }
}
