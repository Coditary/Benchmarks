#[cfg(feature = "zstd")]
pub fn zstd(data: &[u8]) -> Vec<u8> {
    zstd::stream::decode_all(data).expect("decompress output")
}

#[cfg(feature = "gzip")]
pub fn gzip(data: &[u8]) -> Vec<u8> {
    use flate2::read::GzDecoder;
    use std::io::Read;

    let mut decoder = GzDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}

#[cfg(feature = "zlib")]
pub fn zlib(data: &[u8]) -> Vec<u8> {
    use flate2::read::ZlibDecoder;
    use std::io::Read;

    let mut decoder = ZlibDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}

#[cfg(feature = "deflate")]
pub fn deflate(data: &[u8]) -> Vec<u8> {
    use flate2::read::DeflateDecoder;
    use std::io::Read;

    let mut decoder = DeflateDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}

#[cfg(feature = "lz4")]
pub fn lz4(data: &[u8]) -> Vec<u8> {
    lz4_flex::decompress_size_prepended(data).expect("decompress output")
}

#[cfg(feature = "brotli")]
pub fn brotli(data: &[u8]) -> Vec<u8> {
    let mut output = Vec::new();
    brotli::BrotliDecompress(
        &mut std::io::Cursor::new(data),
        &mut output,
    )
    .expect("decompress output");
    output
}

#[cfg(feature = "snappy")]
pub fn snappy(data: &[u8]) -> Vec<u8> {
    snap::raw::Decoder::new()
        .decompress_vec(data)
        .expect("decompress output")
}

#[cfg(feature = "bzip2")]
pub fn bzip2(data: &[u8]) -> Vec<u8> {
    use std::io::Read;

    let mut decoder = bzip2::read::BzDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}

#[cfg(feature = "xz")]
pub fn xz(data: &[u8]) -> Vec<u8> {
    use std::io::Read;

    let mut decoder = xz2::read::XzDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}

#[cfg(feature = "lzma")]
pub fn lzma(data: &[u8]) -> Vec<u8> {
    use std::io::Cursor;

    let mut output = Vec::new();
    lzma_rs::lzma_decompress(&mut Cursor::new(data), &mut output).expect("decompress output");
    output
}
