#[cfg(feature = "zstd")]
pub fn zstd(data: &[u8]) -> Vec<u8> {
    zstd::bulk::compress(data, 3).expect("compress output")
}

#[cfg(feature = "gzip")]
pub fn gzip(data: &[u8]) -> Vec<u8> {
    use flate2::write::GzEncoder;
    use flate2::Compression;
    use std::io::Write;

    let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data).expect("compress output");
    encoder.finish().expect("finish compress output")
}

#[cfg(feature = "zlib")]
pub fn zlib(data: &[u8]) -> Vec<u8> {
    use flate2::write::ZlibEncoder;
    use flate2::Compression;
    use std::io::Write;

    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data).expect("compress output");
    encoder.finish().expect("finish compress output")
}

#[cfg(feature = "deflate")]
pub fn deflate(data: &[u8]) -> Vec<u8> {
    use flate2::write::DeflateEncoder;
    use flate2::Compression;
    use std::io::Write;

    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data).expect("compress output");
    encoder.finish().expect("finish compress output")
}

#[cfg(feature = "lz4")]
pub fn lz4(data: &[u8]) -> Vec<u8> {
    lz4_flex::compress_prepend_size(data)
}

#[cfg(feature = "brotli")]
pub fn brotli(data: &[u8]) -> Vec<u8> {
    let mut output = Vec::new();
    brotli::BrotliCompress(
        &mut std::io::Cursor::new(data),
        &mut output,
        &Default::default(),
    )
    .expect("compress output");
    output
}

#[cfg(feature = "snappy")]
pub fn snappy(data: &[u8]) -> Vec<u8> {
    snap::raw::Encoder::new()
        .compress_vec(data)
        .expect("compress output")
}

#[cfg(feature = "bzip2")]
pub fn bzip2(data: &[u8]) -> Vec<u8> {
    use std::io::Write;

    let mut encoder = bzip2::write::BzEncoder::new(Vec::new(), bzip2::Compression::default());
    encoder.write_all(data).expect("compress output");
    encoder.finish().expect("finish compress output")
}

#[cfg(feature = "xz")]
pub fn xz(data: &[u8]) -> Vec<u8> {
    use std::io::Write;

    let mut output = Vec::new();
    let mut encoder = xz2::write::XzEncoder::new(&mut output, 6);
    encoder.write_all(data).expect("compress output");
    encoder.finish().expect("finish compress output");
    output
}

#[cfg(feature = "lzma")]
pub fn lzma(data: &[u8]) -> Vec<u8> {
    use std::io::Cursor;

    let mut output = Vec::new();
    lzma_rs::lzma_compress(&mut Cursor::new(data), &mut output).expect("compress output");
    output
}
