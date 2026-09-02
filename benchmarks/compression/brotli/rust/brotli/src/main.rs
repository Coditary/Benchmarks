use std::env;
use std::time::Instant;

use bench_support::timing::{print_result, run_with_setup};
use compression_bench_support::compress::brotli;
use compression_bench_support::emit::try_emit_fixture;
use compression_bench_support::payload::load_payload;

fn main() {
    if try_emit_fixture(brotli) {
        return;
    }

    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let payload = load_payload(&spec);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_with_setup(load_seconds, payload, |data| brotli(data));
    print_result(&result);
}
