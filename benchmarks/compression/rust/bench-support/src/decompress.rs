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

#[cfg(any(feature = "lzf", feature = "fastlz", feature = "minilzo"))]
fn original_size(data: &[u8]) -> usize {
    let prefix: [u8; 4] = data[..4].try_into().expect("size prefix");
    u32::from_le_bytes(prefix) as usize
}

#[cfg(feature = "lzf")]
pub fn lzf(data: &[u8]) -> Vec<u8> {
    let original_len = original_size(data);
    lzf::decompress(&data[4..], original_len).expect("decompress output")
}

#[cfg(feature = "fastlz")]
pub fn fastlz(data: &[u8]) -> Vec<u8> {
    let original_len = original_size(data);
    let mut output = vec![0u8; original_len];
    let written_len = fastlz::decompress(&data[4..], &mut output)
        .expect("decompress output")
        .len();
    output.truncate(written_len);
    output
}

#[cfg(feature = "minilzo")]
pub fn minilzo(data: &[u8]) -> Vec<u8> {
    use lzokay::decompress::decompress;

    let original_len = original_size(data);
    let mut output = vec![0u8; original_len];
    let written = decompress(&data[4..], &mut output).expect("decompress output");
    output.truncate(written);
    output
}

#[cfg(feature = "lzfse")]
pub fn lzfse(data: &[u8]) -> Vec<u8> {
    let mut capacity = data.len().max(64) * 4;
    const MAX_CAPACITY: usize = 256 * 1024 * 1024;
    loop {
        let mut output = vec![0u8; capacity];
        match lzfse::decode_buffer(data, &mut output) {
            Ok(written) => {
                if written == 0 {
                    panic!("decompress output: lzfse returned zero bytes");
                }
                output.truncate(written);
                return output;
            }
            Err(lzfse::Error::BufferTooSmall) => {
                capacity = capacity.saturating_mul(2);
                if capacity > MAX_CAPACITY {
                    panic!("decompress output: lzfse output exceeds {MAX_CAPACITY} bytes");
                }
            }
            Err(error) => panic!("decompress output: {error:?}"),
        }
    }
}

#[cfg(feature = "libdeflate")]
pub fn libdeflate(data: &[u8]) -> Vec<u8> {
    let mut decompressor = libdeflater::Decompressor::new();
    let mut capacity = data.len().max(64) * 4;
    const MAX_CAPACITY: usize = 256 * 1024 * 1024;
    loop {
        let mut output = vec![0u8; capacity];
        match decompressor.deflate_decompress(data, &mut output) {
            Ok(written) => {
                output.truncate(written);
                return output;
            }
            Err(libdeflater::DecompressionError::InsufficientSpace) => {
                capacity = capacity.saturating_mul(2);
                if capacity > MAX_CAPACITY {
                    panic!("decompress output: libdeflate output exceeds {MAX_CAPACITY} bytes");
                }
            }
            Err(error) => panic!("decompress output: {error:?}"),
        }
    }
}

#[cfg(feature = "zopfli")]
pub fn zopfli(data: &[u8]) -> Vec<u8> {
    use flate2::read::DeflateDecoder;
    use std::io::Read;

    let mut decoder = DeflateDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}

#[cfg(feature = "zlib-ng")]
pub fn zlib_ng(data: &[u8]) -> Vec<u8> {
    use flate2_zlib_ng::read::ZlibDecoder;
    use std::io::Read;

    let mut decoder = ZlibDecoder::new(data);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .expect("decompress output");
    output
}
