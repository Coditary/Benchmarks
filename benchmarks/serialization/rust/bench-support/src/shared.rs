use std::fs;
use std::path::{Path, PathBuf};

pub fn shared_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../../datasets/shared")
}

pub fn load_canonical_bytes(spec: &str) -> Vec<u8> {
    let path = shared_root().join(spec).join("canonical.json");
    fs::read(&path).unwrap_or_else(|err| {
        panic!("failed to read input {}: {err}", path.display());
    })
}

pub fn domain_from_spec(spec: &str) -> &str {
    spec.split('/').next().unwrap_or(spec)
}
