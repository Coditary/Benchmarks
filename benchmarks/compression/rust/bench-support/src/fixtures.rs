use crate::payload::load_payload;

/// Compressed wire bytes for decompression benchmarks, derived from the canonical
/// or synthetic payload at runtime (no duplicated fixture files required).
pub fn load_fixture_bytes(_codec: &str, spec: &str) -> Vec<u8> {
    let payload = load_payload(spec);
    compress_payload(&payload)
}

#[cfg(feature = "lzma")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::lzma(payload)
}

#[cfg(feature = "xz")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::xz(payload)
}

#[cfg(feature = "bzip2")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::bzip2(payload)
}

#[cfg(feature = "snappy")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::snappy(payload)
}

#[cfg(feature = "brotli")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::brotli(payload)
}

#[cfg(feature = "lz4")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::lz4(payload)
}

#[cfg(feature = "deflate")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::deflate(payload)
}

#[cfg(feature = "zlib")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::zlib(payload)
}

#[cfg(feature = "gzip")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::gzip(payload)
}

#[cfg(feature = "zstd")]
fn compress_payload(payload: &[u8]) -> Vec<u8> {
    crate::compress::zstd(payload)
}

pub fn ensure_parent(path: &std::path::Path) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    Ok(())
}
