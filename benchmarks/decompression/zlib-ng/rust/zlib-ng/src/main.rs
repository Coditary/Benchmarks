use std::env;
use std::time::Instant;

use bench_support::timing::{print_result, run_deserialize_with_setup};
use compression_bench_support::decompress::zlib_ng;
use compression_bench_support::fixtures::load_fixture_bytes;

const CODEC: &str = "zlib-ng";

fn main() {
    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let payload = load_fixture_bytes(CODEC, &spec);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_deserialize_with_setup(load_seconds, payload, |bytes| {
        zlib_ng(bytes)
    });
    print_result(&result);
}
