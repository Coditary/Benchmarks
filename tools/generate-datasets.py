#!/usr/bin/env python3
"""Generate shared benchmark datasets (canonical JSON only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "datasets" / "shared"
INDEX = ROOT / "datasets" / "index.json"

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

AST_MAX_DEPTH = 10

AST_TIERS = {
    "10": 10,
    "100": 100,
    "1000": 1_000,
    "10k": 10_000,
}

ALL_TIERS = sorted(set(RECORD_TIERS) | set(MESH_TIERS) | set(AST_TIERS))

DOMAINS = ["logs", "profile", "mesh", "catalog", "ast"]

AST_NODE_TYPES = ["Program", "Block", "Call", "Member", "Binary", "Unary", "Literal"]

LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
PATHS = [
    "/api/users/{}",
    "/api/orders/{}",
    "/api/products/{}",
    "/api/search?q=bench",
    "/health",
    "/api/auth/login",
]
AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "curl/8.5.0",
    "PostmanRuntime/7.36.0",
    "python-requests/2.31.0",
    "Go-http-client/1.1",
]
CITIES = ["Berlin", "Munich", "Hamburg", "Cologne", "Vienna", "Zurich"]
TAGS = ["admin", "beta", "premium", "verified", "active", "trial"]
PRODUCT_TAGS = ["electronics", "sale", "new", "bestseller", "limited", "eco"]
ATTR_KEYS = ["color", "size", "weight_g", "material", "warranty_years"]


def generate_log_entry(rng: random.Random, index: int) -> dict:
    method = rng.choice(METHODS)
    path = rng.choice(PATHS).format(rng.randint(1, 9999))
    status = rng.choice([200, 201, 204, 301, 400, 401, 404, 500])
    if status >= 500:
        level = "ERROR"
    elif status >= 400:
        level = "WARN"
    else:
        level = rng.choice(LEVELS[:3])

    return {
        "timestamp": f"2024-01-15T{10 + index // 3600:02d}:{(index * 7) % 60:02d}:{(index * 13) % 60:02d}.{index % 1000:03d}Z",
        "level": level,
        "message": f"{method} {path}",
        "request_id": f"{index:08x}-aaaa-bbbb-cccc-{index:012x}",
        "metadata": {
            "status": status,
            "duration_ms": rng.randint(1, 1200),
            "bytes_sent": rng.randint(32, 8192),
            "user_agent": rng.choice(AGENTS),
            "remote_addr": f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        },
    }


def generate_profile(rng: random.Random, index: int) -> dict:
    first = rng.choice(["Alex", "Sam", "Jordan", "Taylor", "Casey", "Morgan"])
    last = rng.choice(["Meyer", "Schmidt", "Weber", "Wagner", "Fischer", "Becker"])
    return {
        "id": f"usr_{index:08d}",
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}{index % 97}@example.com",
        "active": rng.random() > 0.1,
        "tags": rng.sample(TAGS, k=rng.randint(1, 3)),
        "preferences": {
            "locale": rng.choice(["de-DE", "en-US", "fr-FR"]),
            "newsletter": rng.random() > 0.5,
            "theme": rng.choice(["light", "dark", "system"]),
        },
        "address": {
            "city": rng.choice(CITIES),
            "postal_code": f"{rng.randint(10000, 99999)}",
            "country": rng.choice(["DE", "AT", "CH"]),
        },
    }


def generate_product(rng: random.Random, index: int) -> dict:
    keys = rng.sample(ATTR_KEYS, k=rng.randint(2, 4))
    attributes = {
        key: (
            rng.choice(["red", "blue", "green", "black"])
            if key == "color"
            else str(rng.randint(1, 5000))
        )
        for key in keys
    }
    return {
        "sku": f"SKU-{index:08d}",
        "name": f"Product {index}",
        "price_cents": rng.randint(99, 999_99),
        "currency": rng.choice(["EUR", "USD", "CHF"]),
        "in_stock": rng.random() > 0.15,
        "tags": rng.sample(PRODUCT_TAGS, k=rng.randint(1, 3)),
        "attributes": attributes,
    }


def write_canonical_stream(
    path: Path,
    *,
    domain: str,
    tier: str,
    records_key: str,
    count: int,
    rng: random.Random,
    record_factory,
) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    size = 0

    with path.open("w", encoding="utf-8") as handle:
        header = (
            '{\n  "version": 1,\n'
            f'  "domain": "{domain}",\n'
            f'  "tier": "{tier}",\n'
            f'  "{records_key}": [\n'
        )
        handle.write(header)
        hasher.update(header.encode("utf-8"))
        size += len(header.encode("utf-8"))

        for index in range(count):
            record = record_factory(rng, index)
            record_json = json.dumps(record, ensure_ascii=True)
            chunk = ("    " if index == 0 else ",\n    ") + record_json
            handle.write(chunk)
            hasher.update(chunk.encode("utf-8"))
            size += len(chunk.encode("utf-8"))

        footer = "\n  ]\n}\n"
        handle.write(footer)
        hasher.update(footer.encode("utf-8"))
        size += len(footer.encode("utf-8"))

    return {
        "canonical_bytes": size,
        "canonical_sha256": hasher.hexdigest(),
        "record_count": count,
    }


def write_mesh_canonical(path: Path, *, tier: str, vertex_count: int, rng: random.Random) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    size = 0
    triangle_count = max(vertex_count // 3, 1)

    with path.open("w", encoding="utf-8") as handle:
        header = (
            '{\n  "version": 1,\n'
            '  "domain": "mesh",\n'
            f'  "tier": "{tier}",\n'
            f'  "name": "bench-mesh-{tier}",\n'
            '  "vertices": [\n'
        )
        handle.write(header)
        hasher.update(header.encode("utf-8"))
        size += len(header.encode("utf-8"))

        for index in range(vertex_count):
            angle = (index / max(vertex_count, 1)) * math.tau
            radius = 1.0 + (index % 17) * 0.01
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            z = (index % 100) * 0.001
            nx, ny, nz = x, y, z
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            vertex = {
                "x": round(x, 6),
                "y": round(y, 6),
                "z": round(z, 6),
                "nx": round(nx / length, 6),
                "ny": round(ny / length, 6),
                "nz": round(nz / length, 6),
            }
            chunk = ("    " if index == 0 else ",\n    ") + json.dumps(vertex, ensure_ascii=True)
            handle.write(chunk)
            hasher.update(chunk.encode("utf-8"))
            size += len(chunk.encode("utf-8"))

        indices_header = '\n  ],\n  "indices": [\n'
        handle.write(indices_header)
        hasher.update(indices_header.encode("utf-8"))
        size += len(indices_header.encode("utf-8"))

        flat_indices: list[int] = []
        for triangle in range(triangle_count):
            base = (triangle * 3) % max(vertex_count - 2, 1)
            flat_indices.extend([base, base + 1, base + 2])

        for index, value in enumerate(flat_indices):
            chunk = ("    " if index == 0 else ",\n    ") + str(value)
            handle.write(chunk)
            hasher.update(chunk.encode("utf-8"))
            size += len(chunk.encode("utf-8"))

        footer = "\n  ]\n}\n"
        handle.write(footer)
        hasher.update(footer.encode("utf-8"))
        size += len(footer.encode("utf-8"))

    return {
        "canonical_bytes": size,
        "canonical_sha256": hasher.hexdigest(),
        "vertex_count": vertex_count,
        "triangle_count": triangle_count,
    }


def generate_logs(tier: str, count: int, rng: random.Random) -> dict:
    meta = write_canonical_stream(
        SHARED / "logs" / tier / "canonical.json",
        domain="logs",
        tier=tier,
        records_key="entries",
        count=count,
        rng=rng,
        record_factory=generate_log_entry,
    )
    meta["entry_count"] = meta.pop("record_count")
    return meta


def generate_profiles(tier: str, count: int, rng: random.Random) -> dict:
    meta = write_canonical_stream(
        SHARED / "profile" / tier / "canonical.json",
        domain="profile",
        tier=tier,
        records_key="profiles",
        count=count,
        rng=rng,
        record_factory=generate_profile,
    )
    meta["profile_count"] = meta.pop("record_count")
    return meta


def generate_mesh(tier: str, vertex_count: int, rng: random.Random) -> dict:
    return write_mesh_canonical(
        SHARED / "mesh" / tier / "canonical.json",
        tier=tier,
        vertex_count=vertex_count,
        rng=rng,
    )


def generate_catalog(tier: str, count: int, rng: random.Random) -> dict:
    meta = write_canonical_stream(
        SHARED / "catalog" / tier / "canonical.json",
        domain="catalog",
        tier=tier,
        records_key="products",
        count=count,
        rng=rng,
        record_factory=generate_product,
    )
    meta["product_count"] = meta.pop("record_count")
    return meta


def build_ast_chain(*, depth: int, node_id: int) -> tuple[dict, int]:
    node_type = AST_NODE_TYPES[depth % len(AST_NODE_TYPES)]
    node: dict = {
        "node_type": node_type,
        "id": node_id,
        "name": f"node-{depth}",
        "span": {"line": depth + 1, "column": depth * 3},
    }
    if depth <= 0:
        node["value"] = f"leaf-{node_id}"
        node["children"] = []
        return node, node_id + 1

    child, next_id = build_ast_chain(depth=depth - 1, node_id=node_id + 1)
    node["children"] = [child]
    return node, next_id


def build_ast_branching(
    rng: random.Random,
    *,
    depth: int,
    target_depth: int,
    max_children: int,
    node_id: int,
    node_budget: int,
) -> tuple[dict, int, int]:
    node_type = AST_NODE_TYPES[depth % len(AST_NODE_TYPES)]
    node: dict = {
        "node_type": node_type,
        "id": node_id,
        "name": f"node-{depth}",
        "span": {"line": depth + 1, "column": depth * 3},
    }
    next_id = node_id + 1
    remaining_budget = node_budget - 1

    if depth >= target_depth or remaining_budget <= 0:
        node["value"] = f"leaf-{node_id}"
        node["children"] = []
        return node, next_id, remaining_budget

    child_count = 1 if max_children <= 1 else rng.randint(1, max_children)
    child_count = min(child_count, remaining_budget)
    children: list[dict] = []
    for _ in range(child_count):
        child, next_id, remaining_budget = build_ast_branching(
            rng,
            depth=depth + 1,
            target_depth=target_depth,
            max_children=max_children,
            node_id=next_id,
            node_budget=remaining_budget,
        )
        children.append(child)
    node["children"] = children
    return node, next_id, remaining_budget


def generate_ast_tree(rng: random.Random, *, node_id: int) -> tuple[dict, int]:
    shape_roll = rng.random()
    if shape_roll < 0.5:
        target_depth = rng.randint(1, AST_MAX_DEPTH)
        return build_ast_chain(depth=target_depth, node_id=node_id)

    if shape_roll < 0.8:
        target_depth = rng.randint(3, AST_MAX_DEPTH)
        max_children = 2
        node_budget = min(32, 2 ** (target_depth - 1) + 8)
    else:
        target_depth = rng.randint(2, min(5, AST_MAX_DEPTH))
        max_children = rng.randint(3, 5)
        node_budget = 24

    tree, next_id, _ = build_ast_branching(
        rng,
        depth=0,
        target_depth=target_depth,
        max_children=max_children,
        node_id=node_id,
        node_budget=node_budget,
    )
    return tree, next_id


def write_ast_canonical(path: Path, *, tier: str, tree_count: int, rng: random.Random) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    size = 0
    next_node_id = 0

    with path.open("w", encoding="utf-8") as handle:
        header = (
            '{\n  "version": 1,\n'
            '  "domain": "ast",\n'
            f'  "tier": "{tier}",\n'
            f'  "max_depth": {AST_MAX_DEPTH},\n'
            '  "trees": [\n'
        )
        handle.write(header)
        hasher.update(header.encode("utf-8"))
        size += len(header.encode("utf-8"))

        for index in range(tree_count):
            tree, next_node_id = generate_ast_tree(rng, node_id=next_node_id)
            tree_json = json.dumps(tree, ensure_ascii=True)
            chunk = ("    " if index == 0 else ",\n    ") + tree_json
            handle.write(chunk)
            hasher.update(chunk.encode("utf-8"))
            size += len(chunk.encode("utf-8"))

        footer = "\n  ]\n}\n"
        handle.write(footer)
        hasher.update(footer.encode("utf-8"))
        size += len(footer.encode("utf-8"))

    return {
        "canonical_bytes": size,
        "canonical_sha256": hasher.hexdigest(),
        "tree_count": tree_count,
        "max_depth": AST_MAX_DEPTH,
        "node_count": next_node_id,
    }


def generate_ast(tier: str, tree_count: int, rng: random.Random) -> dict:
    return write_ast_canonical(
        SHARED / "ast" / tier / "canonical.json",
        tier=tier,
        tree_count=tree_count,
        rng=rng,
    )


def build_index(generated: dict) -> None:
    existing: dict[str, dict] = {}
    if INDEX.exists():
        existing = json.loads(INDEX.read_text(encoding="utf-8")).get("datasets", {})

    merged = {**existing, **generated}
    for domain in DOMAINS:
        for obsolete in ("xs", "sm", "md", "lg"):
            merged.pop(f"{domain}/{obsolete}", None)
    for obsolete in ("depth-10", "depth-50", "depth-100", "branch-depth-10", "100k"):
        merged.pop(f"ast/{obsolete}", None)
    index = {
        "version": 1,
        "layout": {
            "root": "datasets/shared",
            "path_pattern": "datasets/shared/{domain}/{tier}",
            "input_file": "canonical.json",
            "benchmark_parameter": "{domain}/{tier}",
        },
        "size_tiers": {
            tier: {
                "record_count": count,
                "description": f"{count:,} records (logs, profile, catalog, ast)",
            }
            for tier, count in RECORD_TIERS.items()
        },
        "mesh_tiers": {
            tier: {
                "vertex_count": count,
                "description": f"{count:,} vertices",
            }
            for tier, count in MESH_TIERS.items()
        },
        "domains": {
            "logs": {
                "description": "HTTP request logs with string-heavy metadata.",
                "record_field": "entries",
            },
            "profile": {
                "description": "User profile records with nested objects and tags.",
                "record_field": "profiles",
            },
            "mesh": {
                "description": "3D mesh with float-heavy vertices and triangle indices.",
                "record_field": "vertices",
            },
            "catalog": {
                "description": "Product catalog with prices, tags, and attributes.",
                "record_field": "products",
            },
            "ast": {
                "description": (
                    "AST-like JSON trees (max nesting depth 10) with mixed shapes "
                    "and varying subtree counts per tier (up to 10k trees)."
                ),
                "record_field": "trees",
            },
        },
        "datasets": merged,
    }
    INDEX.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tiers",
        nargs="*",
        default=None,
        choices=ALL_TIERS,
        help="Tiers to generate (default: all applicable tiers per domain).",
    )
    parser.add_argument(
        "--domains",
        nargs="*",
        default=DOMAINS,
        choices=DOMAINS,
        help="Domains to generate (default: all).",
    )
    args = parser.parse_args()

    record_tiers = [tier for tier in (args.tiers or ALL_TIERS) if tier in RECORD_TIERS]
    mesh_tiers = [tier for tier in (args.tiers or ALL_TIERS) if tier in MESH_TIERS]

    generated: dict[str, dict] = {}
    for tier in record_tiers:
        if "logs" in args.domains:
            count = RECORD_TIERS[tier]
            rng = random.Random(42 + count)
            key = f"logs/{tier}"
            generated[key] = generate_logs(tier, count, rng)
            print(f"generated {key}: {generated[key]['entry_count']} entries")

        if "profile" in args.domains:
            count = RECORD_TIERS[tier]
            rng = random.Random(1337 + count)
            key = f"profile/{tier}"
            generated[key] = generate_profiles(tier, count, rng)
            print(f"generated {key}: {generated[key]['profile_count']} profiles")

        if "catalog" in args.domains:
            count = RECORD_TIERS[tier]
            rng = random.Random(4242 + count)
            key = f"catalog/{tier}"
            generated[key] = generate_catalog(tier, count, rng)
            print(f"generated {key}: {generated[key]['product_count']} products")

        if "ast" in args.domains:
            if tier not in AST_TIERS:
                continue
            count = AST_TIERS[tier]
            rng = random.Random(31415 + count)
            key = f"ast/{tier}"
            generated[key] = generate_ast(tier, count, rng)
            print(
                f"generated {key}: {generated[key]['tree_count']} trees, "
                f"{generated[key]['node_count']} nodes, "
                f"max depth {generated[key]['max_depth']}"
            )

    for tier in mesh_tiers:
        if "mesh" in args.domains:
            vertex_count = MESH_TIERS[tier]
            rng = random.Random(9001 + vertex_count)
            key = f"mesh/{tier}"
            generated[key] = generate_mesh(tier, vertex_count, rng)
            print(
                f"generated {key}: {generated[key]['vertex_count']} vertices, "
                f"{generated[key]['triangle_count']} triangles"
            )

    build_index(generated)
    print(f"wrote {INDEX}")


if __name__ == "__main__":
    main()
