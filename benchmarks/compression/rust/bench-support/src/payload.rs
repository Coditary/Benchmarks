use std::path::PathBuf;

fn compression_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../datasets/compression")
}

fn shared_root() -> PathBuf {
    compression_root()
        .parent()
        .expect("datasets root")
        .join("shared")
}

fn is_structured_domain(domain: &str) -> bool {
    matches!(domain, "logs" | "profile" | "catalog" | "mesh")
}

pub fn payload_path(spec: &str) -> PathBuf {
    let (domain, tier) = spec
        .split_once('/')
        .unwrap_or_else(|| panic!("invalid compression spec: {spec}"));
    compression_root().join(domain).join(tier).join("payload.bin")
}

pub fn load_payload(spec: &str) -> Vec<u8> {
    let (domain, tier) = spec
        .split_once('/')
        .unwrap_or_else(|| panic!("invalid compression spec: {spec}"));

    if is_structured_domain(domain) {
        let path = shared_root().join(domain).join(tier).join("canonical.json");
        return std::fs::read(&path).unwrap_or_else(|error| {
            panic!(
                "canonical payload not found at {} (run tools/generate-datasets.py): {error}",
                path.display()
            )
        });
    }

    let path = payload_path(spec);
    std::fs::read(&path).unwrap_or_else(|error| {
        panic!(
            "compression payload not found at {} (run tools/generate-compression-datasets.py): {error}",
            path.display()
        )
    })
}
