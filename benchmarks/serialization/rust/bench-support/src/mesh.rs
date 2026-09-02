use serde::{Deserialize, Serialize};

use crate::shared::load_canonical_bytes;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct Vertex {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub nx: f32,
    pub ny: f32,
    pub nz: f32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct MeshDataset {
    pub version: u32,
    pub domain: String,
    pub tier: String,
    pub name: String,
    pub vertices: Vec<Vertex>,
    pub indices: Vec<u32>,
}

pub fn load(spec: &str) -> MeshDataset {
    let bytes = load_canonical_bytes(spec);
    serde_json::from_slice(&bytes).unwrap_or_else(|err| {
        panic!("failed to parse mesh dataset {spec}: {err}");
    })
}
