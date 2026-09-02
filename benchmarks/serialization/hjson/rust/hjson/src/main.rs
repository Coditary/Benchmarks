use std::env;
use std::time::Instant;

use bench_support::dataset::load;
use bench_support::emit::try_emit_fixture;
use bench_support::serialize::hjson_format;
use bench_support::timing::{print_result, run_with_setup};

fn main() {
    if try_emit_fixture(|data| hjson_format(&data)) {
        return;
    }

    let dataset = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let data = load(&dataset);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_with_setup(load_seconds, data, hjson_format);
    print_result(&result);
}
