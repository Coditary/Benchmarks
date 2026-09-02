use std::env;
use std::fs;
use std::io;
use std::path::Path;

use crate::fixtures::ensure_parent;
use crate::payload::load_payload;

pub fn try_emit_fixture(encode: impl FnOnce(&[u8]) -> Vec<u8>) -> bool {
    let Some((output, spec)) = parse_emit_fixture_args() else {
        return false;
    };
    let bytes = encode(&load_payload(&spec));
    write_fixture(&output, &bytes).expect("write fixture");
    eprintln!("wrote fixture {output} ({} bytes)", bytes.len());
    true
}

pub fn parse_emit_fixture_args() -> Option<(String, String)> {
    let mut args = env::args().skip(1);
    if args.next().as_deref()? != "--emit-fixture" {
        return None;
    }
    let output = args.next()?;
    let spec = args.next()?;
    Some((output, spec))
}

pub fn write_fixture(path: impl AsRef<Path>, bytes: &[u8]) -> io::Result<()> {
    let path = path.as_ref();
    ensure_parent(path)?;
    fs::write(path, bytes)
}
