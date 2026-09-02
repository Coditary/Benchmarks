#!/usr/bin/env python3
"""Generate compression benchmark payloads with different entropy profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "datasets" / "shared"
OUT = ROOT / "datasets" / "compression"
INDEX = OUT / "index.json"

RECORD_TIERS = {
    "10": 10,
    "100": 100,
    "1000": 1_000,
    "10k": 10_000,
    "100k": 100_000,
}

MESH_TIERS = {
    "100": 100,
    "1000": 1_000,
    "10k": 10_000,
    "100k": 100_000,
}

BYTE_TIERS = {
    "64k": 65_536,
    "256k": 262_144,
    "1m": 1_048_576,
    "4m": 4_194_304,
}

AST_TIERS = {
    "10": 10,
    "100": 100,
    "1000": 1_000,
    "10k": 10_000,
}

RECORD_DOMAINS = ("logs", "profile", "catalog")
SYNTHETIC_DOMAINS = ("random", "sparse", "english", "repetitive")

ENGLISH_SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "Benchmark suites should use reproducible deterministic inputs.",
    "Compression performance depends heavily on payload entropy.",
    "Structured logs compress well because fields repeat often.",
    "Random byte streams approximate incompressible network traffic.",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_payload(domain: str, tier: str, payload: bytes, profile: str) -> dict:
    target = OUT / domain / tier
    target.mkdir(parents=True, exist_ok=True)
    path = target / "payload.bin"
    path.write_bytes(payload)
    return {
        "domain": domain,
        "tier": tier,
        "spec": f"{domain}/{tier}",
        "profile": profile,
        "payload_bytes": len(payload),
        "payload_sha256": sha256(payload),
        "path": str(path.relative_to(ROOT)),
    }


def reference_shared(domain: str, tier: str) -> dict:
    source = SHARED / domain / tier / "canonical.json"
    payload = source.read_bytes()
    profiles = {
        "logs": "structured_repetitive_logs",
        "profile": "structured_nested_json",
        "catalog": "structured_key_value_catalog",
        "mesh": "numeric_float_arrays",
        "ast": "deeply_nested_ast_json",
    }
    return {
        "domain": domain,
        "tier": tier,
        "spec": f"{domain}/{tier}",
        "profile": profiles.get(domain, "structured"),
        "payload_bytes": len(payload),
        "payload_sha256": sha256(payload),
        "source": str(source.relative_to(ROOT)),
        "path": str(source.relative_to(ROOT)),
    }


def generate_random(rng: random.Random, size: int) -> bytes:
    return rng.randbytes(size)


def generate_sparse(rng: random.Random, size: int) -> bytes:
    data = bytearray(size)
    for index in range(0, size, 64):
        if rng.random() < 0.08:
            data[index] = rng.randint(1, 255)
    return bytes(data)


def generate_english(rng: random.Random, size: int) -> bytes:
    chunks: list[str] = []
    total = 0
    while total < size:
        sentence = rng.choice(ENGLISH_SENTENCES)
        chunks.append(sentence)
        chunks.append(" ")
        total += len(sentence) + 1
    text = "".join(chunks)
    return text.encode("utf-8")[:size]


def generate_repetitive(_: random.Random, size: int) -> bytes:
    unit = b"REPEATABLE_PATTERN::field=42|status=ok|region=eu-central|"
    return (unit * ((size // len(unit)) + 1))[:size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    entries: list[dict] = []

    for domain in RECORD_DOMAINS:
        for tier in RECORD_TIERS:
            entries.append(reference_shared(domain, tier))

    for tier in AST_TIERS:
        entries.append(reference_shared("ast", tier))

    for tier in MESH_TIERS:
        entries.append(reference_shared("mesh", tier))

    rng = random.Random(0xC0DEC0DE)
    generators = {
        "random": generate_random,
        "sparse": generate_sparse,
        "english": generate_english,
        "repetitive": generate_repetitive,
    }
    profiles = {
        "random": "high_entropy_random",
        "sparse": "sparse_mostly_zeros",
        "english": "natural_language_text",
        "repetitive": "low_entropy_repeated_pattern",
    }
    for domain in SYNTHETIC_DOMAINS:
        for tier, size in BYTE_TIERS.items():
            payload = generators[domain](rng, size)
            entries.append(write_payload(domain, tier, payload, profiles[domain]))

    manifest = {
        "layout": {
            "root": "datasets/compression",
            "path_pattern": "datasets/compression/{domain}/{tier}",
            "input_file": "payload.bin",
            "structured_source_root": "datasets/shared",
            "structured_source_file": "canonical.json",
            "benchmark_parameter": "{domain}/{tier}",
        },
        "domains": {
            "logs": {"profile": "structured_repetitive_logs", "record_field": "entry_count"},
            "profile": {"profile": "structured_nested_json", "record_field": "profile_count"},
            "catalog": {"profile": "structured_key_value_catalog", "record_field": "product_count"},
            "mesh": {"profile": "numeric_float_arrays", "record_field": "vertex_count"},
            "ast": {"profile": "deeply_nested_ast_json", "record_field": "tree_count"},
            "random": {"profile": "high_entropy_random", "record_field": "payload_bytes"},
            "sparse": {"profile": "sparse_mostly_zeros", "record_field": "payload_bytes"},
            "english": {"profile": "natural_language_text", "record_field": "payload_bytes"},
            "repetitive": {"profile": "low_entropy_repeated_pattern", "record_field": "payload_bytes"},
        },
        "datasets": {entry["spec"]: entry for entry in entries},
        "datasets_count": len(entries),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} compression payloads to {OUT}")


if __name__ == "__main__":
    main()
