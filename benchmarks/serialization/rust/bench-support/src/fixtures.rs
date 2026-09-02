use std::path::{Path, PathBuf};

use crate::dataset::{self, Dataset};
use crate::shared::shared_root;

/// Legacy layout kept for `--emit-fixture` and optional cache writers.
pub fn fixtures_root() -> PathBuf {
    shared_root()
        .parent()
        .expect("datasets root")
        .join("fixtures")
}

/// `datasets/fixtures/{format}/{domain}/{tier}/fixture.bin`
pub fn fixture_path(format: &str, spec: &str) -> PathBuf {
    let (domain, tier) = split_spec(spec);
    fixtures_root()
        .join(format)
        .join(domain)
        .join(tier)
        .join("fixture.bin")
}

pub fn split_spec(spec: &str) -> (&str, &str) {
    let (domain, tier) = spec
        .split_once('/')
        .unwrap_or_else(|| panic!("invalid dataset spec: {spec}"));
    (domain, tier)
}

pub fn ensure_parent(path: &Path) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    Ok(())
}

/// Wire-format bytes for deserialization benchmarks, derived from canonical JSON in
/// `datasets/shared/` at runtime (no duplicated fixture files required).
pub fn load_fixture_bytes(_format: &str, spec: &str) -> Vec<u8> {
    encode_wire_dataset(&dataset::load(spec))
}

#[cfg(feature = "ucl")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::ucl(data)
}

#[cfg(feature = "plist")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::plist_format(data)
}

#[cfg(feature = "cjson")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::cjson(data)
}

#[cfg(feature = "hjson")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::hjson_format(data)
}

#[cfg(feature = "json5")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::json5_format(data)
}

#[cfg(feature = "tsv")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::tsv(data)
}

#[cfg(feature = "csv")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::csv(data)
}

#[cfg(feature = "cbor")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::cbor(data)
}

#[cfg(feature = "bson")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::bson(data)
}

#[cfg(feature = "kdl")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::kdl(data)
}

#[cfg(feature = "ini")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::ini(data)
}

#[cfg(feature = "xml")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::xml(data)
}

#[cfg(feature = "toml")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::toml_format(data)
}

#[cfg(feature = "yaml")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::yaml(data)
}

#[cfg(feature = "rmp-serde")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::rmp_serde(data)
}

#[cfg(feature = "flexbuffers")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::flexbuffers(data)
}

#[cfg(feature = "rkyv")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::rkyv(data)
}

#[cfg(feature = "bitcode")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::bitcode(data)
}

#[cfg(feature = "simd-json")]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::simd_json(data)
}

#[cfg(not(any(
    feature = "ucl",
    feature = "plist",
    feature = "cjson",
    feature = "hjson",
    feature = "json5",
    feature = "tsv",
    feature = "csv",
    feature = "cbor",
    feature = "bson",
    feature = "kdl",
    feature = "ini",
    feature = "xml",
    feature = "toml",
    feature = "yaml",
    feature = "rmp-serde",
    feature = "flexbuffers",
    feature = "rkyv",
    feature = "bitcode",
    feature = "simd-json"
)))]
fn encode_wire_dataset(data: &Dataset) -> Vec<u8> {
    crate::serialize::json(data)
}

pub fn record_count_field(domain: &str) -> &'static str {
    match domain {
        "logs" => "entry_count",
        "profile" => "profile_count",
        "catalog" => "product_count",
        "mesh" => "vertex_count",
        "ast" => "tree_count",
        other => panic!("unknown dataset domain: {other}"),
    }
}

pub fn record_count_from_domain(domain: &str, value: usize) -> serde_json::Value {
    serde_json::json!({ record_count_field(domain): value })
}
