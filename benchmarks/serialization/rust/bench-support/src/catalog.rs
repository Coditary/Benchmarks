use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::shared::load_canonical_bytes;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct Product {
    pub sku: String,
    pub name: String,
    pub price_cents: u32,
    pub currency: String,
    pub in_stock: bool,
    pub tags: Vec<String>,
    pub attributes: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct CatalogDataset {
    pub version: u32,
    pub domain: String,
    pub tier: String,
    pub products: Vec<Product>,
}

pub fn load(spec: &str) -> CatalogDataset {
    let bytes = load_canonical_bytes(spec);
    serde_json::from_slice(&bytes).unwrap_or_else(|err| {
        panic!("failed to parse catalog dataset {spec}: {err}");
    })
}
