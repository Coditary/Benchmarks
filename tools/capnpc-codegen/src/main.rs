fn main() {
    capnpc::codegen::CodeGenerationCommand::new()
        .output_directory(std::path::Path::new("."))
        .run(std::io::stdin())
        .expect("failed to generate capnp rust code");
}
