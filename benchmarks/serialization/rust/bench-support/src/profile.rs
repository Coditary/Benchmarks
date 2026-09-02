use serde::{Deserialize, Serialize};

use crate::shared::load_canonical_bytes;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct ProfilePreferences {
    pub locale: String,
    pub newsletter: bool,
    pub theme: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct ProfileAddress {
    pub city: String,
    pub postal_code: String,
    pub country: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct Profile {
    pub id: String,
    pub name: String,
    pub email: String,
    pub active: bool,
    pub tags: Vec<String>,
    pub preferences: ProfilePreferences,
    pub address: ProfileAddress,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct ProfileDataset {
    pub version: u32,
    pub domain: String,
    pub tier: String,
    pub profiles: Vec<Profile>,
}

pub fn load(spec: &str) -> ProfileDataset {
    let bytes = load_canonical_bytes(spec);
    serde_json::from_slice(&bytes).unwrap_or_else(|err| {
        panic!("failed to parse profile dataset {spec}: {err}");
    })
}
