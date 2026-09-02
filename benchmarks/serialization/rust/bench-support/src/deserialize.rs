//! Deserialize wire bytes into canonical `Dataset` value types.
//!
//! Every implementation should return `DecodedDataset` with fully materialized
//! owned Rust structs so comparisons use the same end state.

use crate::catalog::CatalogDataset;
use crate::logs::LogDataset;
use crate::mesh::MeshDataset;
use crate::profile::ProfileDataset;
use crate::shared::domain_from_spec;

#[derive(Debug)]
pub enum DecodedDataset {
    Logs(LogDataset),
    Profile(ProfileDataset),
    Mesh(MeshDataset),
    Catalog(CatalogDataset),
}

pub fn json(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(serde_json::from_slice(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(serde_json::from_slice(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(serde_json::from_slice(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(serde_json::from_slice(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "simd-json")]
pub fn simd_json(spec: &str, bytes: &[u8]) -> DecodedDataset {
    let mut buffer = bytes.to_vec();
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(
            simd_json::serde::from_slice(&mut buffer).expect("decode"),
        ),
        "profile" => DecodedDataset::Profile(
            simd_json::serde::from_slice(&mut buffer).expect("decode"),
        ),
        "mesh" => DecodedDataset::Mesh(
            simd_json::serde::from_slice(&mut buffer).expect("decode"),
        ),
        "catalog" => DecodedDataset::Catalog(
            simd_json::serde::from_slice(&mut buffer).expect("decode"),
        ),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "bitcode")]
pub fn bitcode(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(::bitcode::decode(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(::bitcode::decode(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(::bitcode::decode(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(::bitcode::decode(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "rkyv")]
pub fn rkyv(spec: &str, bytes: &[u8]) -> DecodedDataset {
    use rkyv::api::high::from_bytes;
    use rkyv::rancor::Error;

    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(from_bytes::<LogDataset, Error>(bytes).expect("decode")),
        "profile" => {
            DecodedDataset::Profile(from_bytes::<ProfileDataset, Error>(bytes).expect("decode"))
        }
        "mesh" => DecodedDataset::Mesh(from_bytes::<MeshDataset, Error>(bytes).expect("decode")),
        "catalog" => {
            DecodedDataset::Catalog(from_bytes::<CatalogDataset, Error>(bytes).expect("decode"))
        }
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "flexbuffers")]
pub fn flexbuffers(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(flexbuffers::from_slice(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(flexbuffers::from_slice(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(flexbuffers::from_slice(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(flexbuffers::from_slice(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "rmp-serde")]
pub fn rmp_serde(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(rmp_serde::from_slice(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(rmp_serde::from_slice(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(rmp_serde::from_slice(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(rmp_serde::from_slice(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "yaml")]
pub fn yaml(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(serde_yaml::from_slice(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(serde_yaml::from_slice(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(serde_yaml::from_slice(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(serde_yaml::from_slice(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "toml")]
pub fn toml_format(spec: &str, bytes: &[u8]) -> DecodedDataset {
    let text = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(toml::from_str(text).expect("decode")),
        "profile" => DecodedDataset::Profile(toml::from_str(text).expect("decode")),
        "mesh" => DecodedDataset::Mesh(toml::from_str(text).expect("decode")),
        "catalog" => DecodedDataset::Catalog(toml::from_str(text).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "xml")]
pub fn xml(spec: &str, bytes: &[u8]) -> DecodedDataset {
    crate::text_xml::decode(spec, bytes)
}

#[cfg(feature = "ini")]
pub fn ini(spec: &str, bytes: &[u8]) -> DecodedDataset {
    crate::text_ini::decode(spec, bytes)
}

#[cfg(feature = "kdl")]
pub fn kdl(spec: &str, bytes: &[u8]) -> DecodedDataset {
    crate::text_kdl::decode(spec, bytes)
}

#[cfg(feature = "bson")]
pub fn bson(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(::bson::from_slice(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(::bson::from_slice(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(::bson::from_slice(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(::bson::from_slice(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "cbor")]
pub fn cbor(spec: &str, bytes: &[u8]) -> DecodedDataset {
    use ciborium::from_reader;
    use std::io::Cursor;
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(from_reader(Cursor::new(bytes)).expect("decode")),
        "profile" => DecodedDataset::Profile(from_reader(Cursor::new(bytes)).expect("decode")),
        "mesh" => DecodedDataset::Mesh(from_reader(Cursor::new(bytes)).expect("decode")),
        "catalog" => DecodedDataset::Catalog(from_reader(Cursor::new(bytes)).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "csv")]
pub fn csv(spec: &str, bytes: &[u8]) -> DecodedDataset {
    crate::text_csv::decode(spec, bytes, crate::text_csv::Delimiter::Comma)
}

#[cfg(feature = "tsv")]
pub fn tsv(spec: &str, bytes: &[u8]) -> DecodedDataset {
    crate::text_csv::decode(spec, bytes, crate::text_csv::Delimiter::Tab)
}

#[cfg(feature = "json5")]
pub fn json5_format(spec: &str, bytes: &[u8]) -> DecodedDataset {
    let text = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(::json5::from_str(text).expect("decode")),
        "profile" => DecodedDataset::Profile(::json5::from_str(text).expect("decode")),
        "mesh" => DecodedDataset::Mesh(::json5::from_str(text).expect("decode")),
        "catalog" => DecodedDataset::Catalog(::json5::from_str(text).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "hjson")]
pub fn hjson_format(spec: &str, bytes: &[u8]) -> DecodedDataset {
    let text = std::str::from_utf8(bytes).expect("utf-8 fixture");
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(::serde_hjson::from_str(text).expect("decode")),
        "profile" => DecodedDataset::Profile(::serde_hjson::from_str(text).expect("decode")),
        "mesh" => DecodedDataset::Mesh(::serde_hjson::from_str(text).expect("decode")),
        "catalog" => DecodedDataset::Catalog(::serde_hjson::from_str(text).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "cjson")]
pub fn cjson(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(sonic_rs::from_slice(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(sonic_rs::from_slice(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(sonic_rs::from_slice(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(sonic_rs::from_slice(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "plist")]
pub fn plist_format(spec: &str, bytes: &[u8]) -> DecodedDataset {
    match domain_from_spec(spec) {
        "logs" => DecodedDataset::Logs(::plist::from_reader_xml(bytes).expect("decode")),
        "profile" => DecodedDataset::Profile(::plist::from_reader_xml(bytes).expect("decode")),
        "mesh" => DecodedDataset::Mesh(::plist::from_reader_xml(bytes).expect("decode")),
        "catalog" => DecodedDataset::Catalog(::plist::from_reader_xml(bytes).expect("decode")),
        other => panic!("unknown dataset domain: {other}"),
    }
}

#[cfg(feature = "ucl")]
pub fn ucl(spec: &str, bytes: &[u8]) -> DecodedDataset {
    crate::text_ucl::decode(spec, bytes)
}
