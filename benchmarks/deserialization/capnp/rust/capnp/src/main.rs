mod benchmark_capnp {
    include!(concat!(env!("OUT_DIR"), "/benchmark_capnp.rs"));
}

mod serialize;

use std::env;
use std::time::Instant;

use bench_support::dataset::load;
use bench_support::timing::{print_result, run_deserialize_with_setup};

mod deserialize;

use serialize::serialize;

fn main() {
    let spec = env::args().nth(1).expect("usage: bench <domain>/<tier>");
    let load_start = Instant::now();
    let data = load(&spec);
    let payload = serialize(&data);
    let load_seconds = load_start.elapsed().as_secs_f64();

    let result = run_deserialize_with_setup(load_seconds, payload, |bytes| {
        deserialize::decode(&spec, bytes)
    });
    print_result(&result);
}
