fn main() {
    let schema = "../../../../../datasets/shared/schemas/benchmark.proto";
    prost_build::Config::new()
        .compile_protos(&[schema], &["../../../../../datasets/shared/schemas"])
        .expect("compile protobuf schema");
}
