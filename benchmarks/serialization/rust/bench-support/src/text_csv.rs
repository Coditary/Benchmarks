use std::collections::BTreeMap;

use crate::catalog::{CatalogDataset, Product};
use crate::deserialize::DecodedDataset;
use crate::dataset::Dataset;
use crate::logs::{LogDataset, LogEntry, LogMetadata};
use crate::mesh::{MeshDataset, Vertex};
use crate::profile::{Profile, ProfileAddress, ProfileDataset, ProfilePreferences};
use crate::shared::domain_from_spec;

#[derive(Clone, Copy, Debug)]
pub enum Delimiter {
    Comma,
    Tab,
}

pub fn encode(data: &Dataset, delimiter: Delimiter) -> Vec<u8> {
    let text = match data {
        Dataset::Logs(value) => encode_logs(value, delimiter),
        Dataset::Profile(value) => encode_profile(value, delimiter),
        Dataset::Mesh(value) => encode_mesh(value, delimiter),
        Dataset::Catalog(value) => encode_catalog(value, delimiter),
    };
    text.into_bytes()
}

pub fn decode(spec: &str, bytes: &[u8], delimiter: Delimiter) -> DecodedDataset {
    let text = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(decode_logs(text, delimiter)),
        "profile" => DecodedDataset::Profile(decode_profile(text, delimiter)),
        "mesh" => DecodedDataset::Mesh(decode_mesh(text, delimiter)),
        "catalog" => DecodedDataset::Catalog(decode_catalog(text, delimiter)),
        other => panic!("unknown dataset domain: {other}"),
    }
}

fn delimiter_char(delimiter: Delimiter) -> char {
    match delimiter {
        Delimiter::Comma => ',',
        Delimiter::Tab => '\t',
    }
}

fn needs_quoting(value: &str, delimiter: char) -> bool {
    value.contains(delimiter)
        || value.contains(',')
        || value.contains(['\n', '\r', '"'])
}

fn escape_field(value: &str, delimiter: char) -> String {
    if needs_quoting(value, delimiter) {
        format!("\"{}\"", value.replace('"', "\"\""))
    } else {
        value.to_string()
    }
}

fn write_row(out: &mut String, fields: &[&str], delimiter: Delimiter) {
    let delim = delimiter_char(delimiter);
    for (index, field) in fields.iter().enumerate() {
        if index > 0 {
            out.push(delim);
        }
        out.push_str(&escape_field(field, delim));
    }
    out.push('\n');
}

fn join_pipe(values: &[String]) -> String {
    values.join("|")
}

fn encode_attributes(attributes: &BTreeMap<String, String>) -> String {
    attributes
        .iter()
        .map(|(key, value)| format!("{key}={value}"))
        .collect::<Vec<_>>()
        .join("|")
}

fn encode_logs(data: &LogDataset, delimiter: Delimiter) -> String {
    let mut out = String::new();
    write_row(
        &mut out,
        &[
            "version",
            "domain",
            "tier",
            "timestamp",
            "level",
            "message",
            "request_id",
            "status",
            "duration_ms",
            "bytes_sent",
            "user_agent",
            "remote_addr",
        ],
        delimiter,
    );
    for entry in &data.entries {
        write_row(
            &mut out,
            &[
                &data.version.to_string(),
                &data.domain,
                &data.tier,
                &entry.timestamp,
                &entry.level,
                &entry.message,
                &entry.request_id,
                &entry.metadata.status.to_string(),
                &entry.metadata.duration_ms.to_string(),
                &entry.metadata.bytes_sent.to_string(),
                &entry.metadata.user_agent,
                &entry.metadata.remote_addr,
            ],
            delimiter,
        );
    }
    out
}

fn encode_profile(data: &ProfileDataset, delimiter: Delimiter) -> String {
    let mut out = String::new();
    write_row(
        &mut out,
        &[
            "version",
            "domain",
            "tier",
            "id",
            "name",
            "email",
            "active",
            "tags",
            "locale",
            "newsletter",
            "theme",
            "city",
            "postal_code",
            "country",
        ],
        delimiter,
    );
    for profile in &data.profiles {
        write_row(
            &mut out,
            &[
                &data.version.to_string(),
                &data.domain,
                &data.tier,
                &profile.id,
                &profile.name,
                &profile.email,
                if profile.active { "true" } else { "false" },
                &join_pipe(&profile.tags),
                &profile.preferences.locale,
                if profile.preferences.newsletter {
                    "true"
                } else {
                    "false"
                },
                &profile.preferences.theme,
                &profile.address.city,
                &profile.address.postal_code,
                &profile.address.country,
            ],
            delimiter,
        );
    }
    out
}

fn encode_mesh(data: &MeshDataset, delimiter: Delimiter) -> String {
    let mut out = String::new();
    out.push_str("#meta\n");
    write_row(
        &mut out,
        &["version", "domain", "tier", "name"],
        delimiter,
    );
    write_row(
        &mut out,
        &[
            &data.version.to_string(),
            &data.domain,
            &data.tier,
            &data.name,
        ],
        delimiter,
    );
    out.push_str("#vertices\n");
    write_row(&mut out, &["x", "y", "z", "nx", "ny", "nz"], delimiter);
    for vertex in &data.vertices {
        write_row(
            &mut out,
            &[
                &vertex.x.to_string(),
                &vertex.y.to_string(),
                &vertex.z.to_string(),
                &vertex.nx.to_string(),
                &vertex.ny.to_string(),
                &vertex.nz.to_string(),
            ],
            delimiter,
        );
    }
    out.push_str("#indices\n");
    write_row(&mut out, &["index"], delimiter);
    for index in &data.indices {
        write_row(&mut out, &[&index.to_string()], delimiter);
    }
    out
}

fn encode_catalog(data: &CatalogDataset, delimiter: Delimiter) -> String {
    let mut out = String::new();
    write_row(
        &mut out,
        &[
            "version",
            "domain",
            "tier",
            "sku",
            "name",
            "price_cents",
            "currency",
            "in_stock",
            "tags",
            "attributes",
        ],
        delimiter,
    );
    for product in &data.products {
        write_row(
            &mut out,
            &[
                &data.version.to_string(),
                &data.domain,
                &data.tier,
                &product.sku,
                &product.name,
                &product.price_cents.to_string(),
                &product.currency,
                if product.in_stock { "true" } else { "false" },
                &join_pipe(&product.tags),
                &encode_attributes(&product.attributes),
            ],
            delimiter,
        );
    }
    out
}

fn parse_csv_records(text: &str, delimiter: char) -> Vec<Vec<String>> {
    let mut records = Vec::new();
    let mut current_record = Vec::new();
    let mut current_field = String::new();
    let mut in_quotes = false;
    let mut chars = text.chars().peekable();

    while let Some(ch) = chars.next() {
        if in_quotes {
            match ch {
                '"' => {
                    if chars.peek() == Some(&'"') {
                        chars.next();
                        current_field.push('"');
                    } else {
                        in_quotes = false;
                    }
                }
                other => current_field.push(other),
            }
            continue;
        }

        match ch {
            '"' => in_quotes = true,
            ch if ch == delimiter => {
                current_record.push(current_field);
                current_field = String::new();
            }
            '\n' => {
                current_record.push(current_field);
                current_field = String::new();
                records.push(current_record);
                current_record = Vec::new();
            }
            '\r' => {}
            other => current_field.push(other),
        }
    }

    if in_quotes {
        panic!("unterminated quoted field");
    }
    if !current_field.is_empty() || !current_record.is_empty() {
        current_record.push(current_field);
        records.push(current_record);
    }

    records
}

fn field_at(fields: &[String], index: usize, label: &str) -> String {
    fields
        .get(index)
        .cloned()
        .unwrap_or_else(|| panic!("missing field {label}"))
}

fn parse_u32(value: &str, label: &str) -> u32 {
    value.parse().unwrap_or_else(|_| panic!("invalid u32 for {label}"))
}

fn parse_u16(value: &str, label: &str) -> u16 {
    parse_u32(value, label) as u16
}

fn parse_f32(value: &str, label: &str) -> f32 {
    value.parse().unwrap_or_else(|_| panic!("invalid f32 for {label}"))
}

fn parse_bool(value: &str, label: &str) -> bool {
    match value {
        "true" | "1" | "yes" => true,
        "false" | "0" | "no" => false,
        other => panic!("invalid bool for {label}: {other}"),
    }
}

fn parse_pipe_list(value: &str) -> Vec<String> {
    if value.is_empty() {
        Vec::new()
    } else {
        value.split('|').map(str::to_string).collect()
    }
}

fn parse_attributes(value: &str) -> BTreeMap<String, String> {
    let mut attributes = BTreeMap::new();
    if value.is_empty() {
        return attributes;
    }
    for pair in value.split('|') {
        let (key, value) = pair
            .split_once('=')
            .unwrap_or_else(|| panic!("invalid attribute pair: {pair}"));
        attributes.insert(key.to_string(), value.to_string());
    }
    attributes
}

fn decode_logs(text: &str, delimiter: Delimiter) -> LogDataset {
    let delim = delimiter_char(delimiter);
    let records = parse_csv_records(text, delim);
    if records.len() < 2 {
        panic!("missing logs data rows");
    }
    let first_data = &records[1];
    let version = parse_u32(&field_at(first_data, 0, "version"), "version");
    let domain = field_at(first_data, 1, "domain");
    let tier = field_at(first_data, 2, "tier");
    let entries = records
        .into_iter()
        .skip(1)
        .map(|row| {
            LogEntry {
                timestamp: field_at(&row, 3, "timestamp"),
                level: field_at(&row, 4, "level"),
                message: field_at(&row, 5, "message"),
                request_id: field_at(&row, 6, "request_id"),
                metadata: LogMetadata {
                    status: parse_u16(&field_at(&row, 7, "status"), "status"),
                    duration_ms: parse_u32(&field_at(&row, 8, "duration_ms"), "duration_ms"),
                    bytes_sent: parse_u32(&field_at(&row, 9, "bytes_sent"), "bytes_sent"),
                    user_agent: field_at(&row, 10, "user_agent"),
                    remote_addr: field_at(&row, 11, "remote_addr"),
                },
            }
        })
        .collect();
    LogDataset {
        version,
        domain,
        tier,
        entries,
    }
}

fn decode_profile(text: &str, delimiter: Delimiter) -> ProfileDataset {
    let delim = delimiter_char(delimiter);
    let records = parse_csv_records(text, delim);
    if records.len() < 2 {
        panic!("missing profile data rows");
    }
    let first_data = &records[1];
    let version = parse_u32(&field_at(first_data, 0, "version"), "version");
    let domain = field_at(first_data, 1, "domain");
    let tier = field_at(first_data, 2, "tier");
    let profiles = records
        .into_iter()
        .skip(1)
        .map(|row| {
            Profile {
                id: field_at(&row, 3, "id"),
                name: field_at(&row, 4, "name"),
                email: field_at(&row, 5, "email"),
                active: parse_bool(&field_at(&row, 6, "active"), "active"),
                tags: parse_pipe_list(&field_at(&row, 7, "tags")),
                preferences: ProfilePreferences {
                    locale: field_at(&row, 8, "locale"),
                    newsletter: parse_bool(&field_at(&row, 9, "newsletter"), "newsletter"),
                    theme: field_at(&row, 10, "theme"),
                },
                address: ProfileAddress {
                    city: field_at(&row, 11, "city"),
                    postal_code: field_at(&row, 12, "postal_code"),
                    country: field_at(&row, 13, "country"),
                },
            }
        })
        .collect();
    ProfileDataset {
        version,
        domain,
        tier,
        profiles,
    }
}

fn decode_mesh(text: &str, delimiter: Delimiter) -> MeshDataset {
    let delim = delimiter_char(delimiter);
    let mut version = None;
    let mut domain = String::new();
    let mut tier = String::new();
    let mut name = String::new();
    let mut vertices = Vec::new();
    let mut indices = Vec::new();
    let mut lines = text.lines().peekable();

    while let Some(line) = lines.next() {
        if line.is_empty() {
            continue;
        }
        match line {
            "#meta" => {
                lines.next().expect("missing meta header");
                let data_line = lines.next().expect("missing meta row");
                let fields = parse_csv_records(data_line, delim)
                    .into_iter()
                    .next()
                    .unwrap_or_else(|| panic!("missing meta row"));
                version = Some(parse_u32(&field_at(&fields, 0, "version"), "version"));
                domain = field_at(&fields, 1, "domain");
                tier = field_at(&fields, 2, "tier");
                name = field_at(&fields, 3, "name");
            }
            "#vertices" => {
                lines.next().expect("missing vertices header");
                while let Some(next) = lines.peek() {
                    if next.is_empty() {
                        lines.next();
                        continue;
                    }
                    if next.starts_with('#') {
                        break;
                    }
                    let row_line = lines.next().expect("vertex row");
                    let fields = parse_csv_records(row_line, delim)
                        .into_iter()
                        .next()
                        .unwrap_or_else(|| panic!("missing vertex row"));
                    vertices.push(Vertex {
                        x: parse_f32(&field_at(&fields, 0, "x"), "x"),
                        y: parse_f32(&field_at(&fields, 1, "y"), "y"),
                        z: parse_f32(&field_at(&fields, 2, "z"), "z"),
                        nx: parse_f32(&field_at(&fields, 3, "nx"), "nx"),
                        ny: parse_f32(&field_at(&fields, 4, "ny"), "ny"),
                        nz: parse_f32(&field_at(&fields, 5, "nz"), "nz"),
                    });
                }
            }
            "#indices" => {
                lines.next().expect("missing indices header");
                while let Some(next) = lines.peek() {
                    if next.is_empty() {
                        lines.next();
                        continue;
                    }
                    if next.starts_with('#') {
                        break;
                    }
                    let row_line = lines.next().expect("index row");
                    let fields = parse_csv_records(row_line, delim)
                        .into_iter()
                        .next()
                        .unwrap_or_else(|| panic!("missing index row"));
                    indices.push(parse_u32(&field_at(&fields, 0, "index"), "index"));
                }
            }
            other => panic!("unexpected mesh line: {other}"),
        }
    }

    if version.is_none() {
        panic!("missing mesh #meta section");
    }

    MeshDataset {
        version: version.expect("version"),
        domain,
        tier,
        name,
        vertices,
        indices,
    }
}

fn decode_catalog(text: &str, delimiter: Delimiter) -> CatalogDataset {
    let delim = delimiter_char(delimiter);
    let records = parse_csv_records(text, delim);
    if records.len() < 2 {
        panic!("missing catalog data rows");
    }
    let first_data = &records[1];
    let version = parse_u32(&field_at(first_data, 0, "version"), "version");
    let domain = field_at(first_data, 1, "domain");
    let tier = field_at(first_data, 2, "tier");
    let products = records
        .into_iter()
        .skip(1)
        .map(|row| {
            Product {
                sku: field_at(&row, 3, "sku"),
                name: field_at(&row, 4, "name"),
                price_cents: parse_u32(&field_at(&row, 5, "price_cents"), "price_cents"),
                currency: field_at(&row, 6, "currency"),
                in_stock: parse_bool(&field_at(&row, 7, "in_stock"), "in_stock"),
                tags: parse_pipe_list(&field_at(&row, 8, "tags")),
                attributes: parse_attributes(&field_at(&row, 9, "attributes")),
            }
        })
        .collect();
    CatalogDataset {
        version,
        domain,
        tier,
        products,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dataset::Dataset;

    fn roundtrip(spec: &str, delimiter: Delimiter) {
        let data = crate::dataset::load(spec);
        let bytes = encode(&data, delimiter);
        let decoded = decode(spec, &bytes, delimiter);
        match (data, decoded) {
            (Dataset::Logs(expected), DecodedDataset::Logs(actual)) => {
                assert_eq!(expected.version, actual.version);
                assert_eq!(expected.entries.len(), actual.entries.len());
            }
            (Dataset::Profile(expected), DecodedDataset::Profile(actual)) => {
                assert_eq!(expected.profiles.len(), actual.profiles.len());
            }
            (Dataset::Mesh(expected), DecodedDataset::Mesh(actual)) => {
                assert_eq!(expected.vertices.len(), actual.vertices.len());
                assert_eq!(expected.indices.len(), actual.indices.len());
            }
            (Dataset::Catalog(expected), DecodedDataset::Catalog(actual)) => {
                assert_eq!(expected.products.len(), actual.products.len());
            }
            _ => panic!("domain mismatch"),
        }
    }

    #[test]
    fn csv_roundtrip_small_fixtures() {
        for spec in ["logs/10", "profile/10", "mesh/100", "catalog/10"] {
            roundtrip(spec, Delimiter::Comma);
            roundtrip(spec, Delimiter::Tab);
        }
    }
}
