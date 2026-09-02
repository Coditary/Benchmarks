fn main() {
    let manifest_dir =
        std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"));
    let generated = manifest_dir.join("generated/benchmark_generated.rs");
    let out_dir = std::path::PathBuf::from(std::env::var("OUT_DIR").expect("OUT_DIR"));
    std::fs::copy(&generated, out_dir.join("benchmark_generated.rs"))
        .expect("copy committed flatbuffers generated code");
    println!("cargo:rerun-if-changed={}", generated.display());
}
