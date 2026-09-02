use serde::{Deserialize, Serialize};

use crate::shared::load_canonical_bytes;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct LogMetadata {
    pub status: u16,
    pub duration_ms: u32,
    pub bytes_sent: u32,
    pub user_agent: String,
    pub remote_addr: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct LogEntry {
    pub timestamp: String,
    pub level: String,
    pub message: String,
    pub request_id: String,
    pub metadata: LogMetadata,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct LogDataset {
    pub version: u32,
    pub domain: String,
    pub tier: String,
    pub entries: Vec<LogEntry>,
}

pub fn load(spec: &str) -> LogDataset {
    let bytes = load_canonical_bytes(spec);
    serde_json::from_slice(&bytes).unwrap_or_else(|err| {
        panic!("failed to parse logs dataset {spec}: {err}");
    })
}
