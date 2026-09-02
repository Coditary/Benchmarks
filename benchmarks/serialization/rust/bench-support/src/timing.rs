use std::env;
use std::io::Write;
use std::time::Instant;

use flate2::write::GzEncoder;
use flate2::Compression;

pub struct BenchResult {
    pub mean_seconds: f64,
    pub median_seconds: f64,
    pub stddev_seconds: f64,
    pub min_seconds: f64,
    pub max_seconds: f64,
    pub runs: u32,
    pub warmup: u32,
    pub load_seconds: f64,
    pub output_bytes: usize,
    pub output_gzip_bytes: usize,
    pub peak_memory_bytes: u64,
    pub cv_percent: f64,
    pub spread_percent: f64,
    pub load_serialize_ratio: f64,
    pub input_bytes: usize,
    pub load_deserialize_ratio: f64,
}

pub fn bench_settings() -> (u32, u32) {
    let warmup = env::var("BENCH_WARMUP")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(3);
    let runs = env::var("BENCH_RUNS")
        .ok()
        .and_then(|value| value.parse().ok())
        .or_else(|| {
            env::var("BENCH_MAX_RUNS")
                .ok()
                .and_then(|value| value.parse().ok())
        })
        .unwrap_or(50);
    (warmup, runs)
}

fn median(samples: &mut [f64]) -> f64 {
    samples.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mid = samples.len() / 2;
    if samples.len() % 2 == 0 {
        (samples[mid - 1] + samples[mid]) / 2.0
    } else {
        samples[mid]
    }
}

fn stddev(samples: &[f64], mean: f64) -> f64 {
    if samples.len() < 2 {
        return 0.0;
    }
    let variance = samples
        .iter()
        .map(|value| {
            let delta = value - mean;
            delta * delta
        })
        .sum::<f64>()
        / samples.len() as f64;
    variance.sqrt()
}

fn current_rss_bytes() -> u64 {
    #[cfg(target_os = "linux")]
    {
        if let Ok(statm) = std::fs::read_to_string("/proc/self/statm") {
            if let Some(rss_pages) = statm.split_whitespace().nth(1) {
                if let Ok(pages) = rss_pages.parse::<u64>() {
                    return pages * page_size_bytes();
                }
            }
        }
    }
    0
}

fn page_size_bytes() -> u64 {
    #[cfg(target_os = "linux")]
    {
        let page_size = unsafe { libc::sysconf(libc::_SC_PAGESIZE) };
        if page_size > 0 {
            return page_size as u64;
        }
    }
    4096
}

fn gzip_size(data: &[u8]) -> usize {
    let mut encoder = GzEncoder::new(Vec::new(), Compression::fast());
    encoder.write_all(data).expect("gzip output");
    encoder.finish().expect("finish gzip output").len()
}

pub fn run_with_setup<Prepared, Serialize>(
    load_seconds_before_setup: f64,
    prepared: Prepared,
    serialize: Serialize,
) -> BenchResult
where
    Serialize: Fn(&Prepared) -> Vec<u8>,
{
    let (warmup, runs) = bench_settings();
    let mut peak_memory_bytes = current_rss_bytes();

    for _ in 0..warmup {
        let output = serialize(&prepared);
        std::hint::black_box(&output);
        peak_memory_bytes = peak_memory_bytes.max(current_rss_bytes());
    }

    let mut samples = Vec::with_capacity(runs as usize);
    let mut last_output = Vec::new();
    for _ in 0..runs {
        let start = Instant::now();
        let output = serialize(&prepared);
        last_output = output;
        std::hint::black_box(&last_output);
        samples.push(start.elapsed().as_secs_f64());
        peak_memory_bytes = peak_memory_bytes.max(current_rss_bytes());
    }

    let mean = samples.iter().sum::<f64>() / samples.len() as f64;
    let mut sorted = samples.clone();
    let median_value = median(&mut sorted);
    let stddev_value = stddev(&samples, mean);
    let min_value = sorted.first().copied().unwrap_or(0.0);
    let max_value = sorted.last().copied().unwrap_or(0.0);
    let cv_percent = if mean > 0.0 {
        (stddev_value / mean) * 100.0
    } else {
        0.0
    };
    let spread_percent = if mean > 0.0 {
        ((max_value - min_value) / mean) * 100.0
    } else {
        0.0
    };
    let load_serialize_ratio = if mean > 0.0 {
        load_seconds_before_setup / mean
    } else {
        0.0
    };

    BenchResult {
        mean_seconds: mean,
        median_seconds: median_value,
        stddev_seconds: stddev_value,
        min_seconds: min_value,
        max_seconds: max_value,
        runs,
        warmup,
        load_seconds: load_seconds_before_setup,
        output_bytes: last_output.len(),
        output_gzip_bytes: gzip_size(&last_output),
        peak_memory_bytes,
        cv_percent,
        spread_percent,
        load_serialize_ratio,
        input_bytes: 0,
        load_deserialize_ratio: 0.0,
    }
}

pub fn run_deserialize_with_setup<Decode, Decoded>(
    load_seconds_before_setup: f64,
    payload: Vec<u8>,
    decode: Decode,
) -> BenchResult
where
    Decode: Fn(&[u8]) -> Decoded,
{
    let (warmup, runs) = bench_settings();
    let input_bytes = payload.len();
    let mut peak_memory_bytes = current_rss_bytes();

    for _ in 0..warmup {
        let decoded = decode(&payload);
        std::hint::black_box(&decoded);
        peak_memory_bytes = peak_memory_bytes.max(current_rss_bytes());
    }

    let mut samples = Vec::with_capacity(runs as usize);
    for _ in 0..runs {
        let start = Instant::now();
        let decoded = decode(&payload);
        std::hint::black_box(&decoded);
        samples.push(start.elapsed().as_secs_f64());
        peak_memory_bytes = peak_memory_bytes.max(current_rss_bytes());
    }

    let mean = samples.iter().sum::<f64>() / samples.len() as f64;
    let mut sorted = samples.clone();
    let median_value = median(&mut sorted);
    let stddev_value = stddev(&samples, mean);
    let min_value = sorted.first().copied().unwrap_or(0.0);
    let max_value = sorted.last().copied().unwrap_or(0.0);
    let cv_percent = if mean > 0.0 {
        (stddev_value / mean) * 100.0
    } else {
        0.0
    };
    let spread_percent = if mean > 0.0 {
        ((max_value - min_value) / mean) * 100.0
    } else {
        0.0
    };
    let load_deserialize_ratio = if mean > 0.0 {
        load_seconds_before_setup / mean
    } else {
        0.0
    };

    BenchResult {
        mean_seconds: mean,
        median_seconds: median_value,
        stddev_seconds: stddev_value,
        min_seconds: min_value,
        max_seconds: max_value,
        runs,
        warmup,
        load_seconds: load_seconds_before_setup,
        output_bytes: input_bytes,
        output_gzip_bytes: gzip_size(&payload),
        peak_memory_bytes,
        cv_percent,
        spread_percent,
        load_serialize_ratio: 0.0,
        input_bytes,
        load_deserialize_ratio,
    }
}

pub fn print_result(result: &BenchResult) {
    let payload = serde_json::json!({
        "mean_seconds": result.mean_seconds,
        "median_seconds": result.median_seconds,
        "stddev_seconds": result.stddev_seconds,
        "min_seconds": result.min_seconds,
        "max_seconds": result.max_seconds,
        "runs": result.runs,
        "warmup": result.warmup,
        "load_seconds": result.load_seconds,
        "output_bytes": result.output_bytes,
        "output_gzip_bytes": result.output_gzip_bytes,
        "peak_memory_bytes": result.peak_memory_bytes,
        "cv_percent": result.cv_percent,
        "spread_percent": result.spread_percent,
        "load_serialize_ratio": result.load_serialize_ratio,
        "input_bytes": result.input_bytes,
        "load_deserialize_ratio": result.load_deserialize_ratio,
    });
    println!("{}", payload);
}
