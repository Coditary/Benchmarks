use serde::{Deserialize, Serialize};

use crate::shared::load_canonical_bytes;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct AstSpan {
    pub line: u32,
    pub column: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct AstNode {
    pub node_type: String,
    pub id: u64,
    pub name: String,
    pub span: AstSpan,
    #[serde(default)]
    pub value: Option<String>,
    #[serde(default)]
    pub children: Vec<Box<AstNode>>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[cfg_attr(feature = "bitcode", derive(bitcode::Encode, bitcode::Decode))]
#[cfg_attr(
    feature = "rkyv",
    derive(rkyv::Archive, rkyv::Serialize, rkyv::Deserialize)
)]
pub struct AstDataset {
    pub version: u32,
    pub domain: String,
    pub tier: String,
    pub max_depth: u32,
    pub trees: Vec<AstNode>,
}

pub fn load(spec: &str) -> AstDataset {
    let bytes = load_canonical_bytes(spec);
    serde_json::from_slice(&bytes).unwrap_or_else(|err| {
        panic!("failed to parse ast dataset {spec}: {err}");
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(feature = "rmp-serde")]
    #[test]
    fn rmp_roundtrip_leaf_node() {
        let node = AstNode {
            node_type: "Literal".into(),
            id: 1,
            name: "node-0".into(),
            span: AstSpan { line: 1, column: 0 },
            value: Some("leaf-1".into()),
            children: Vec::new(),
        };
        let bytes = rmp_serde::to_vec(&node).expect("encode");
        let _: AstNode = rmp_serde::from_slice(&bytes).expect("decode leaf");
    }

    #[cfg(feature = "rmp-serde")]
    #[test]
    fn rmp_roundtrip_nested_node() {
        let leaf = AstNode {
            node_type: "Literal".into(),
            id: 1,
            name: "node-1".into(),
            span: AstSpan { line: 2, column: 3 },
            value: Some("leaf-1".into()),
            children: Vec::new(),
        };
        let node = AstNode {
            node_type: "Program".into(),
            id: 0,
            name: "node-0".into(),
            span: AstSpan { line: 1, column: 0 },
            value: None,
            children: vec![Box::new(leaf)],
        };
        let bytes = rmp_serde::to_vec(&node).expect("encode");
        let _: AstNode = rmp_serde::from_slice(&bytes).expect("decode nested");
    }

    #[cfg(feature = "rmp-serde")]
    #[test]
    fn rmp_roundtrip_ast_10() {
        let data = load("ast/10");
        let bytes = rmp_serde::to_vec(&data).expect("encode");
        let _: AstDataset = rmp_serde::from_slice(&bytes).expect("decode");
    }
}
