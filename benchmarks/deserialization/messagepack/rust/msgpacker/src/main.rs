use std::env;
use std::time::Instant;

use bench_support::dataset::load;
use bench_support::timing::{print_result, run_deserialize_with_setup};

mod convert;

fn main() {
    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let data = load(&spec);
    let payload = convert::encode(&convert::prepare(data));
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_deserialize_with_setup(load_seconds, payload, |bytes| {
        convert::decode(&spec, bytes)
    });
    print_result(&result);
}
