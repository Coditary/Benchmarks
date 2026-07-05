#!/usr/bin/env python3
"""Generate markdown and interactive HTML benchmark reports."""

from __future__ import annotations

import html
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(os.getenv("BENCHMARK_ROOT", Path(__file__).resolve().parents[1]))
REPORT_ROOT = ROOT / "reports"

STATIC_METRICS = (
    ("lines_of_code", "Lines of code", "lines", False),
    ("artifact_size_bytes", "Artifact size", "bytes", False),
    ("build_time_ms", "Build time", "ms", True),
)


@dataclass(frozen=True)
class Entry:
    label: str
    lang: str
    impl: str
    domain: str
    test: str
    report_path: Path
    data: dict[str, Any]


def discover_reports() -> list[Entry]:
    entries_by_key: dict[tuple[str, str, str, str], Entry] = {}
    search_paths = [ROOT / "benchmarks", ROOT / "published" / "benchmarks"]

    for base in search_paths:
        if not base.exists():
            continue
        for report_path in sorted(base.rglob("artifacts/report.json")):
            with report_path.open(encoding="utf-8") as handle:
                data = json.load(handle)

            key = (
                data.get("domain", "unknown"),
                data.get("test", "unknown"),
                data.get("lang", "unknown"),
                data.get("impl", "unknown"),
            )
            label = (
                f"{data.get('language', data.get('lang', 'unknown'))}/"
                f"{data.get('implementation', data.get('impl', 'unknown'))}"
            )
            entries_by_key[key] = Entry(
                label=label,
                lang=data.get("language", data.get("lang", "unknown")),
                impl=data.get("implementation", data.get("impl", "unknown")),
                domain=key[0],
                test=key[1],
                report_path=report_path,
                data=data,
            )

    return list(entries_by_key.values())


def group_by_task(entries: list[Entry]) -> dict[tuple[str, str], list[Entry]]:
    grouped: dict[tuple[str, str], list[Entry]] = defaultdict(list)
    for entry in entries:
        grouped[(entry.domain, entry.test)].append(entry)
    return grouped


def result_rows(entry: Entry) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in entry.data.get("metrics", {}).get("hyperfine_results", []):
        size = str(row.get("parameter_size", ""))
        if size:
            rows[size] = row
    return rows


def static_metrics(entry: Entry) -> dict[str, float | int]:
    metrics = entry.data.get("metrics", {})
    return {
        "lines_of_code": int(metrics.get("lines_of_code", 0)),
        "artifact_size_bytes": int(metrics.get("artifact_size_bytes", 0)),
        "build_time_ms": float(metrics.get("build_time_ms", 0)),
    }


def format_bytes(value: Any) -> str:
    try:
        return f"{int(value):,} bytes"
    except (TypeError, ValueError):
        return "-"


def format_bytes_human(value: Any) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "-"

    if amount < 1024:
        return f"{int(amount)} B"
    if amount < 1024**2:
        return f"{amount / 1024:.2f} KB"
    if amount < 1024**3:
        return f"{amount / (1024**2):.2f} MB"
    return f"{amount / (1024**3):.2f} GB"


def format_recorded_at(value: Any) -> str:
    if not value or value == "unknown":
        return "unknown"
    try:
        normalized = str(value).replace("Z", "+00:00")
        recorded = datetime.fromisoformat(normalized)
        if recorded.tzinfo is not None:
            recorded = recorded.astimezone(timezone.utc).replace(tzinfo=None)
        return recorded.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(value)


def project_relative_path(path: Path | str) -> str:
    parts = Path(path).parts
    for anchor in ("benchmarks", "published"):
        if anchor in parts:
            idx = parts.index(anchor)
            return str(Path(*parts[idx:]))
    return Path(path).name


def format_ms(value: Any) -> str:
    try:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return "-"
        return f"{float(value) * 1000:.4f} ms"
    except (TypeError, ValueError):
        return "-"


def format_number(value: Any, suffix: str = "") -> str:
    try:
        number = float(value)
        if suffix == "ms":
            return f"{number:.4f} ms"
        if suffix == "bytes":
            return f"{int(number):,} bytes"
        if suffix == "lines":
            return str(int(number))
        if number == int(number):
            return f"{int(number)}{suffix}"
        return f"{number:.4f}{suffix}"
    except (TypeError, ValueError):
        return "-"


def sorted_sizes(entries: list[Entry]) -> list[str]:
    return sorted(
        {size for entry in entries for size in result_rows(entry)},
        key=lambda value: int(value) if value.isdigit() else value,
    )


def winner_by_size(
    entries: list[Entry], size: str, metric: str
) -> tuple[str, Any] | None:
    best_label = None
    best_value = None

    for entry in entries:
        row = result_rows(entry).get(size)
        if not row:
            continue

        if metric == "mean":
            value = float(row.get("mean", "inf"))
        elif metric == "peak_memory_bytes":
            value = int(row.get("peak_memory_bytes", 2**62))
        else:
            continue

        if best_value is None or value < best_value:
            best_value = value
            best_label = entry.label

    if best_label is None:
        return None
    return best_label, best_value


def winner_static(
    entries: list[Entry],
    metric: str,
    *,
    exclude_zero: bool = False,
) -> tuple[str, Any] | None:
    best_label = None
    best_value = None

    for entry in entries:
        value = static_metrics(entry)[metric]
        if exclude_zero and float(value) <= 0:
            continue
        if best_value is None or value < best_value:
            best_value = value
            best_label = entry.label

    if best_label is None:
        return None
    return best_label, best_value


def build_warnings(entries: list[Entry]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []

    cpu_models = sorted(
        {entry.data.get("env", {}).get("cpu_model", "unknown") for entry in entries}
    )
    if len(cpu_models) > 1:
        warnings.append(
            {
                "level": "error",
                "message": "CPU models differ across implementations; runtime comparisons may be invalid.",
                "details": ", ".join(cpu_models),
            }
        )

    total_ram = sorted(
        {entry.data.get("env", {}).get("total_ram_bytes") for entry in entries}
    )
    if len(total_ram) > 1:
        warnings.append(
            {
                "level": "error",
                "message": "Total system RAM differs across recorded environments.",
                "details": ", ".join(format_bytes(value) for value in total_ram),
            }
        )

    ci_values = {entry.data.get("env", {}).get("is_ci") for entry in entries}
    if len(ci_values) > 1:
        warnings.append(
            {
                "level": "warn",
                "message": "Mixed CI and local runs detected in the same task report.",
                "details": "Prefer comparing results recorded on the same runner type.",
            }
        )

    for entry in entries:
        env = entry.data.get("env", {})
        load = float(env.get("system_load_1min", 0))
        threads = max(int(env.get("logical_threads", 1)), 1)
        if load > threads * 0.75:
            warnings.append(
                {
                    "level": "warn",
                    "message": f"{entry.label}: high 1-minute load average during measurement.",
                    "details": f"load={load:.2f}, logical_threads={threads}",
                }
            )

        ram_usage = float(env.get("ram_usage_percent", 0))
        if ram_usage >= 85:
            warnings.append(
                {
                    "level": "warn",
                    "message": f"{entry.label}: system RAM usage was already high at measurement time.",
                    "details": (
                        f"{ram_usage:.1f}% used, "
                        f"{format_bytes(env.get('available_ram_bytes', 0))} available"
                    ),
                }
            )

        governor = env.get("cpu_governor", "unknown")
        if governor not in {"unknown", "performance"}:
            warnings.append(
                {
                    "level": "info",
                    "message": f"{entry.label}: CPU governor was '{governor}'.",
                    "details": "Performance-sensitive comparisons may be affected.",
                }
            )

    return warnings


def chart_payload(domain: str, test: str, entries: list[Entry]) -> dict[str, Any]:
    sizes = sorted_sizes(entries)
    datasets = []

    for entry in sorted(entries, key=lambda item: item.label.lower()):
        runtime = []
        memory = []
        for size in sizes:
            row = result_rows(entry).get(size, {})
            runtime.append(
                round(float(row["mean"]) * 1000, 4) if row.get("mean") else None
            )
            memory.append(
                int(row["peak_memory_bytes"]) if row.get("peak_memory_bytes") else None
            )

        env = entry.data.get("env", {})
        metrics = entry.data.get("metrics", {})
        hyperfine_results = metrics.get("hyperfine_results", [])
        datasets.append(
            {
                "label": entry.label,
                "lang": entry.lang,
                "runtime": runtime,
                "memory": memory,
                "static": static_metrics(entry),
                "details": {
                    "git_hash": entry.data.get("git_hash", "unknown"),
                    "recorded_at": entry.data.get("recorded_at", "unknown"),
                    "recorded_at_display": format_recorded_at(
                        entry.data.get("recorded_at", "unknown")
                    ),
                    "notes": entry.data.get("notes", ""),
                    "tags": entry.data.get("tags", []),
                    "report_path": project_relative_path(entry.report_path),
                    "task_config": entry.data.get("task_config", {}),
                    "env": env,
                    "hyperfine_results": hyperfine_results,
                },
            }
        )

    return {
        "domain": domain,
        "test": test,
        "sizes": sizes,
        "datasets": datasets,
        "warnings": build_warnings(entries),
        "static_metrics": [
            {"key": key, "label": label, "unit": unit, "exclude_zero_option": exclude_zero}
            for key, label, unit, exclude_zero in STATIC_METRICS
        ],
    }


def build_task_markdown(domain: str, test: str, entries: list[Entry]) -> str:
    sizes = sorted_sizes(entries)
    lines = [
        f"# {domain} / {test}",
        "",
        f"Generated at {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    warnings = build_warnings(entries)
    if warnings:
        lines.extend(["## Comparability warnings", ""])
        for warning in warnings:
            lines.append(f"- **{warning['level'].upper()}**: {warning['message']} {warning.get('details', '')}")
        lines.append("")

    lines.extend(["## Static metric winners", ""])
    lines.append("| Metric | Winner | Value |")
    lines.append("| --- | --- | --- |")
    for key, label, unit, exclude_zero in STATIC_METRICS:
        result = winner_static(entries, key, exclude_zero=exclude_zero)
        if not result:
            lines.append(f"| {label} | - | - |")
            continue
        winner_label, value = result
        lines.append(f"| {label} | {winner_label} | {format_number(value, unit)} |")

    lines.extend(["", "## Runtime winners (mean)", ""])
    lines.append("| Size | Winner | Mean |")
    lines.append("| --- | --- | --- |")
    for size in sizes:
        result = winner_by_size(entries, size, "mean")
        if result:
            label, value = result
            lines.append(f"| {size} | {label} | {format_ms(value)} |")

    lines.extend(["", "## Memory winners (peak RSS)", ""])
    lines.append("| Size | Winner | Peak memory |")
    lines.append("| --- | --- | --- |")
    for size in sizes:
        result = winner_by_size(entries, size, "peak_memory_bytes")
        if result:
            label, value = result
            lines.append(f"| {size} | {label} | {format_bytes(value)} |")

    lines.extend(["", "## Full comparison", ""])
    lines.append(
        "| Implementation | LoC | Artifact | Build time | Size | Mean | Peak memory |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for entry in sorted(entries, key=lambda item: item.label.lower()):
        static = static_metrics(entry)
        for size in sizes:
            row = result_rows(entry).get(size, {})
            lines.append(
                f"| {entry.label} | {static['lines_of_code']} | "
                f"{format_bytes(static['artifact_size_bytes'])} | "
                f"{format_number(static['build_time_ms'], 'ms')} | {size} | "
                f"{format_ms(row.get('mean'))} | {format_bytes(row.get('peak_memory_bytes'))} |"
            )

    lines.extend(["", "## Implementation details", ""])
    for entry in sorted(entries, key=lambda item: item.label.lower()):
        env = entry.data.get("env", {})
        lines.extend(
            [
                f"### {entry.label}",
                "",
                f"- Git hash: `{entry.data.get('git_hash', 'unknown')}`",
                f"- Recorded at: `{format_recorded_at(entry.data.get('recorded_at', 'unknown'))}`",
                f"- Notes: {entry.data.get('notes', '') or '-'}",
                f"- CPU: {env.get('cpu_model', 'unknown')}",
                f"- OS: {env.get('os', 'unknown')}",
                f"- RAM total: {format_bytes_human(env.get('total_ram_bytes', 0))}",
                f"- RAM available at start: {format_bytes_human(env.get('available_ram_bytes', 0))}",
                f"- RAM usage at start: {env.get('ram_usage_percent', 'unknown')}%",
                f"- Load avg (1 min): {env.get('system_load_1min', 'unknown')}",
                f"- CPU governor: {env.get('cpu_governor', 'unknown')}",
                f"- CI run: {env.get('is_ci', False)}",
                f"- Source report: `{project_relative_path(entry.report_path)}`",
                "",
            ]
        )

    return "\n".join(lines)


def build_task_html(domain: str, test: str, entries: list[Entry]) -> str:
    payload_json = json.dumps(chart_payload(domain, test, entries))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(domain)} / {html.escape(test)} benchmark report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      color-scheme: light dark;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --border: #1f2937;
      --panel: rgba(17, 24, 39, 0.92);
      --warn: #fbbf24;
      --error: #fb7185;
      --info: #38bdf8;
    }}
    body {{
      margin: 0;
      font-family: Inter, system-ui, sans-serif;
      background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
      color: var(--text);
    }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 2rem; }}
    h1, h2, h3 {{ margin: 0 0 1rem; }}
    p, .muted {{ color: var(--muted); }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
    }}
    .controls {{ display: flex; flex-wrap: wrap; gap: 0.75rem 1rem; margin-bottom: 1rem; }}
    .toggle {{
      display: inline-flex; align-items: center; gap: 0.5rem;
      padding: 0.45rem 0.75rem; border-radius: 999px;
      border: 1px solid var(--border); background: #0b1220;
      cursor: pointer; user-select: none;
    }}
    .toggle input {{ accent-color: var(--accent); }}
    .grid-2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
    canvas {{ width: 100% !important; height: 360px !important; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--border); padding: 0.65rem 0.5rem; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .warning {{
      border-left: 4px solid var(--warn);
      padding: 0.75rem 1rem; margin-bottom: 0.75rem;
      background: rgba(251, 191, 36, 0.08); border-radius: 8px;
    }}
    .warning.error {{ border-left-color: var(--error); background: rgba(251, 113, 133, 0.08); }}
    .warning.info {{ border-left-color: var(--info); background: rgba(56, 189, 248, 0.08); }}
    details {{
      border: 1px solid var(--border); border-radius: 12px;
      padding: 0.75rem 1rem; margin-bottom: 0.75rem; background: #0b1220;
    }}
    summary {{ cursor: pointer; font-weight: 600; }}
    code {{ color: #7dd3fc; }}
    .stat-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.75rem; margin-top: 0.75rem;
    }}
    .stat-card {{
      border: 1px solid var(--border); border-radius: 10px; padding: 0.75rem;
      background: rgba(15, 23, 42, 0.8); min-width: 0;
    }}
    .stat-card strong {{
      display: block; color: var(--muted); font-size: 0.85rem; margin-bottom: 0.35rem;
    }}
    .stat-card .value {{
      display: block; font-size: 0.95rem; line-height: 1.35; word-break: break-word;
    }}
    .detail-filters {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .detail-filters label {{
      display: flex; flex-direction: column; gap: 0.35rem;
      color: var(--muted); font-size: 0.85rem;
    }}
    .detail-filters input, .detail-filters select {{
      padding: 0.55rem 0.7rem;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: #0b1220;
      color: var(--text);
    }}
    .detail-filters .wide {{ grid-column: 1 / -1; }}
    .filter-actions {{ display: flex; gap: 0.75rem; align-items: end; flex-wrap: wrap; }}
    button.secondary {{
      padding: 0.55rem 0.9rem;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: #0b1220;
      color: var(--text);
      cursor: pointer;
    }}
    .detail-entry[hidden] {{ display: none; }}
    #details-empty {{ color: var(--muted); padding: 0.5rem 0; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(domain)} / {html.escape(test)}</h1>
    <p>Compare runtime, memory, code size, artifact size, and build time. Use the detail panels to inspect measurement context.</p>

    <section class="panel" id="warnings-panel" hidden>
      <h2>Comparability warnings</h2>
      <div id="warnings"></div>
    </section>

    <section class="panel">
      <h2>Filters</h2>
      <div class="controls" id="language-controls"></div>
      <div class="controls" id="implementation-controls"></div>
      <label class="toggle">
        <input type="checkbox" id="build-time-nonzero-only">
        Build time chart: only compare entries with build time &gt; 0
      </label>
    </section>

    <section class="panel grid-2">
      <div><h2>Runtime</h2><canvas id="runtime-chart"></canvas></div>
      <div><h2>Peak memory</h2><canvas id="memory-chart"></canvas></div>
    </section>

    <section class="panel">
      <h2>Static metrics</h2>
      <div class="grid-2">
        <div><h3>Lines of code</h3><canvas id="loc-chart"></canvas></div>
        <div><h3>Artifact size</h3><canvas id="artifact-chart"></canvas></div>
        <div><h3>Build time</h3><canvas id="build-chart"></canvas></div>
      </div>
    </section>

    <section class="panel">
      <h2>Winners</h2>
      <div id="winner-table"></div>
    </section>

    <section class="panel">
      <h2>Implementation details</h2>
      <p class="muted">Search and filter implementations, then expand an entry to inspect metadata, environment, and raw per-size statistics.</p>
      <div class="detail-filters">
        <label class="wide">
          Search
          <input type="search" id="detail-search" placeholder="Language, implementation, notes, tags...">
        </label>
        <label>
          Max peak memory (MB)
          <input type="number" id="detail-max-memory" min="0" step="0.1" placeholder="e.g. 128">
        </label>
        <label>
          Max runtime (ms)
          <input type="number" id="detail-max-runtime" min="0" step="0.01" placeholder="e.g. 50">
        </label>
        <label>
          Apply limits at size
          <select id="detail-size-filter"></select>
        </label>
        <div class="filter-actions">
          <button type="button" class="secondary" id="detail-clear-filters">Clear filters</button>
          <span class="muted" id="detail-match-count"></span>
        </div>
      </div>
      <div id="details"></div>
      <p id="details-empty" hidden>No implementations match your filters.</p>
    </section>
  </main>

  <script>
    const payload = {payload_json};
    const palette = [
      "#38bdf8", "#f472b6", "#34d399", "#fbbf24", "#a78bfa",
      "#fb7185", "#22d3ee", "#4ade80", "#f97316", "#c084fc"
    ];

    const hiddenLabels = new Set();
    const hiddenLangs = new Set();
    let buildTimeNonZeroOnly = false;

    function visibleDatasets() {{
      return payload.datasets.filter((dataset) =>
        !hiddenLabels.has(dataset.label) && !hiddenLangs.has(dataset.lang)
      );
    }}

    function formatBytes(value) {{
      return formatBytesHuman(value);
    }}

    function formatBytesHuman(value) {{
      if (value == null || value === "") return "-";
      const bytes = Number(value);
      if (Number.isNaN(bytes)) return "-";
      if (bytes < 1024) return `${{bytes}} B`;
      if (bytes < 1024 * 1024) return `${{(bytes / 1024).toFixed(2)}} KB`;
      if (bytes < 1024 * 1024 * 1024) return `${{(bytes / (1024 * 1024)).toFixed(2)}} MB`;
      return `${{(bytes / (1024 * 1024 * 1024)).toFixed(2)}} GB`;
    }}

    function formatDateTime(value) {{
      if (!value || value === "unknown") return "unknown";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      const pad = (part) => String(part).padStart(2, "0");
      return `${{date.getFullYear()}}-${{pad(date.getMonth() + 1)}}-${{pad(date.getDate())}} ${{pad(date.getHours())}}:${{pad(date.getMinutes())}}:${{pad(date.getSeconds())}}`;
    }}

    function formatMs(value) {{
      if (value == null || value === "") return "-";
      const ms = Number(value);
      if (Number.isNaN(ms)) return "-";
      return `${{ms.toFixed(4)}} ms`;
    }}

    function formatSecondsAsMs(value) {{
      if (value == null || value === "") return "-";
      const seconds = Number(value);
      if (Number.isNaN(seconds)) return "-";
      return `${{(seconds * 1000).toFixed(4)}} ms`;
    }}

    function runtimeMsFromMean(value) {{
      if (value == null || value === "") return null;
      const seconds = Number(value);
      if (Number.isNaN(seconds)) return null;
      return seconds * 1000;
    }}

    function datasetMetricAtSize(dataset, sizeFilter, metric) {{
      const results = dataset.details.hyperfine_results || [];
      if (sizeFilter === "all") {{
        const values = results.map((row) => {{
          if (metric === "memory") return Number(row.peak_memory_bytes) || 0;
          return runtimeMsFromMean(row.mean) || 0;
        }}).filter((value) => value > 0);
        return values.length ? Math.max(...values) : Infinity;
      }}

      const row = results.find((entry) => String(entry.parameter_size) === sizeFilter);
      if (!row) return Infinity;
      if (metric === "memory") return Number(row.peak_memory_bytes) || Infinity;
      return runtimeMsFromMean(row.mean) ?? Infinity;
    }}

    function matchesDetailFilters(dataset) {{
      const search = document.getElementById("detail-search").value.trim().toLowerCase();
      const maxMemMb = parseFloat(document.getElementById("detail-max-memory").value);
      const maxRuntimeMs = parseFloat(document.getElementById("detail-max-runtime").value);
      const sizeFilter = document.getElementById("detail-size-filter").value;

      if (search) {{
        const haystack = [
          dataset.label,
          dataset.lang,
          dataset.details.notes || "",
          ...(dataset.details.tags || [])
        ].join(" ").toLowerCase();
        if (!haystack.includes(search)) return false;
      }}

      if (!Number.isNaN(maxMemMb) && maxMemMb > 0) {{
        const peakBytes = datasetMetricAtSize(dataset, sizeFilter, "memory");
        if (peakBytes > maxMemMb * 1024 * 1024) return false;
      }}

      if (!Number.isNaN(maxRuntimeMs) && maxRuntimeMs > 0) {{
        const runtime = datasetMetricAtSize(dataset, sizeFilter, "runtime");
        if (runtime > maxRuntimeMs) return false;
      }}

      return true;
    }}

    function applyDetailFilters() {{
      let visibleCount = 0;
      document.querySelectorAll(".detail-entry").forEach((element) => {{
        const dataset = payload.datasets.find((entry) => entry.label === element.dataset.label);
        const show = Boolean(dataset && matchesDetailFilters(dataset));
        element.hidden = !show;
        if (show) visibleCount += 1;
      }});
      document.getElementById("details-empty").hidden = visibleCount > 0;
      document.getElementById("detail-match-count").textContent =
        `${{visibleCount}} / ${{payload.datasets.length}} shown`;
    }}

    function renderWarnings() {{
      const panel = document.getElementById("warnings-panel");
      const container = document.getElementById("warnings");
      if (!payload.warnings.length) {{
        panel.hidden = true;
        return;
      }}
      panel.hidden = false;
      container.innerHTML = payload.warnings.map((warning) =>
        `<div class="warning ${{warning.level}}"><strong>${{warning.level.toUpperCase()}}</strong>: ${{warning.message}}<div class="muted">${{warning.details || ""}}</div></div>`
      ).join("");
    }}

    function makeLineChart(canvasId, metric, yTitle) {{
      const chart = new Chart(document.getElementById(canvasId), {{
        type: "line",
        data: {{ labels: payload.sizes, datasets: [] }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          interaction: {{ mode: "index", intersect: false }},
          plugins: {{ legend: {{ labels: {{ color: "#e5e7eb" }} }} }},
          scales: {{
            x: {{ ticks: {{ color: "#94a3b8" }}, grid: {{ color: "rgba(148,163,184,0.15)" }} }},
            y: {{
              title: {{ display: true, text: yTitle, color: "#94a3b8" }},
              ticks: {{ color: "#94a3b8" }},
              grid: {{ color: "rgba(148,163,184,0.15)" }}
            }}
          }}
        }}
      }});

      return () => {{
        chart.data.datasets = visibleDatasets().map((dataset, index) => ({{
          label: dataset.label,
          data: dataset[metric],
          borderColor: palette[index % palette.length],
          backgroundColor: palette[index % palette.length],
          tension: 0.25,
          spanGaps: true
        }}));
        chart.update();
      }};
    }}

    function makeBarChart(canvasId, metricKey) {{
      const chart = new Chart(document.getElementById(canvasId), {{
        type: "bar",
        data: {{ labels: [], datasets: [{{ label: metricKey, data: [], backgroundColor: [] }}] }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: "#94a3b8" }}, grid: {{ display: false }} }},
            y: {{
              beginAtZero: true,
              ticks: {{ color: "#94a3b8" }},
              grid: {{ color: "rgba(148,163,184,0.15)" }}
            }}
          }}
        }}
      }});

      return () => {{
        let datasets = visibleDatasets();
        if (metricKey === "build_time_ms" && buildTimeNonZeroOnly) {{
          datasets = datasets.filter((dataset) => Number(dataset.static.build_time_ms) > 0);
        }}
        chart.data.labels = datasets.map((dataset) => dataset.label);
        chart.data.datasets[0].data = datasets.map((dataset) => dataset.static[metricKey]);
        chart.data.datasets[0].backgroundColor = datasets.map((_, index) => palette[index % palette.length]);
        chart.update();
      }};
    }}

    const refreshRuntime = makeLineChart("runtime-chart", "runtime", "Milliseconds");
    const refreshMemory = makeLineChart("memory-chart", "memory", "Bytes");
    const refreshLoc = makeBarChart("loc-chart", "lines_of_code");
    const refreshArtifact = makeBarChart("artifact-chart", "artifact_size_bytes");
    const refreshBuild = makeBarChart("build-chart", "build_time_ms");

    function winnerStatic(metricKey, excludeZero = false) {{
      let best = null;
      visibleDatasets().forEach((dataset) => {{
        const value = Number(dataset.static[metricKey]);
        if (excludeZero && value <= 0) return;
        if (!best || value < best.value) best = {{ label: dataset.label, value }};
      }});
      return best;
    }}

    function winnerBySize(size, metric) {{
      let best = null;
      visibleDatasets().forEach((dataset) => {{
        const index = payload.sizes.indexOf(size);
        const value = dataset[metric][index];
        if (value == null) return;
        if (!best || value < best.value) best = {{ label: dataset.label, value }};
      }});
      return best;
    }}

    function renderWinnerTable() {{
      const staticRows = payload.static_metrics.map((metric) => {{
        const best = winnerStatic(metric.key, metric.exclude_zero_option);
        let display = "-";
        if (best) {{
          display = metric.unit === "bytes"
            ? `${{best.label}} (${{formatBytes(best.value)}})`
            : metric.unit === "ms"
              ? `${{best.label}} (${{formatMs(best.value)}})`
              : `${{best.label}} (${{best.value}})`;
        }}
        return `<tr><td>${{metric.label}}</td><td colspan="2">${{display}}</td></tr>`;
      }}).join("");

      const sizeRows = payload.sizes.map((size) => {{
        const bestRuntime = winnerBySize(size, "runtime");
        const bestMemory = winnerBySize(size, "memory");
        return `<tr>
          <td>${{size}}</td>
          <td>${{bestRuntime ? `${{bestRuntime.label}} (${{formatMs(bestRuntime.value)}})` : "-"}}</td>
          <td>${{bestMemory ? `${{bestMemory.label}} (${{formatBytes(bestMemory.value)}})` : "-"}}</td>
        </tr>`;
      }}).join("");

      document.getElementById("winner-table").innerHTML = `
        <table>
          <thead><tr><th>Metric</th><th colspan="2">Winner</th></tr></thead>
          <tbody>${{staticRows}}</tbody>
        </table>
        <table style="margin-top: 1rem;">
          <thead><tr><th>Size</th><th>Fastest runtime</th><th>Lowest memory</th></tr></thead>
          <tbody>${{sizeRows}}</tbody>
        </table>`;
    }}

    function renderDetails() {{
      document.getElementById("details").innerHTML = payload.datasets.map((dataset) => {{
        const env = dataset.details.env || {{}};
        const rows = (dataset.details.hyperfine_results || []).map((row) => `
          <tr>
            <td>${{row.parameter_size}}</td>
            <td>${{formatSecondsAsMs(row.mean)}}</td>
            <td>${{row.stddev ? (Number(row.stddev) * 1000).toFixed(4) + " ms" : "-"}}</td>
            <td>${{formatBytesHuman(row.peak_memory_bytes)}}</td>
            <td>${{row.min ? formatSecondsAsMs(row.min) : "-"}}</td>
            <td>${{row.max ? formatSecondsAsMs(row.max) : "-"}}</td>
          </tr>`).join("");

        const tags = (dataset.details.tags || []).map((tag) => `<code>${{tag}}</code>`).join(" ");
        const recordedAt = dataset.details.recorded_at_display || formatDateTime(dataset.details.recorded_at);
        return `
          <details class="detail-entry" data-label="${{dataset.label}}">
            <summary>${{dataset.label}}</summary>
            <div class="stat-grid">
              <div class="stat-card"><strong>Git hash</strong><span class="value">${{dataset.details.git_hash || "unknown"}}</span></div>
              <div class="stat-card"><strong>Recorded at</strong><span class="value">${{recordedAt}}</span></div>
              <div class="stat-card"><strong>CPU</strong><span class="value">${{env.cpu_model || "unknown"}}</span></div>
              <div class="stat-card"><strong>OS</strong><span class="value">${{env.os || "unknown"}}</span></div>
              <div class="stat-card"><strong>Total RAM</strong><span class="value">${{formatBytesHuman(env.total_ram_bytes)}}</span></div>
              <div class="stat-card"><strong>Available RAM at start</strong><span class="value">${{formatBytesHuman(env.available_ram_bytes)}}</span></div>
              <div class="stat-card"><strong>RAM usage at start</strong><span class="value">${{env.ram_usage_percent ?? "unknown"}}%</span></div>
              <div class="stat-card"><strong>Load avg (1 min)</strong><span class="value">${{env.system_load_1min ?? "unknown"}}</span></div>
              <div class="stat-card"><strong>CPU governor</strong><span class="value">${{env.cpu_governor || "unknown"}}</span></div>
              <div class="stat-card"><strong>Runner</strong><span class="value">${{env.is_ci ? "CI (" + (env.runner_name || "unknown") + ")" : "local"}}</span></div>
              <div class="stat-card"><strong>Lines of code</strong><span class="value">${{dataset.static.lines_of_code}}</span></div>
              <div class="stat-card"><strong>Artifact size</strong><span class="value">${{formatBytesHuman(dataset.static.artifact_size_bytes)}}</span></div>
              <div class="stat-card"><strong>Build time</strong><span class="value">${{formatMs(dataset.static.build_time_ms)}}</span></div>
            </div>
            <p style="margin-top: 1rem;"><strong>Notes:</strong> ${{dataset.details.notes || "-"}}</p>
            <p class="muted">Tags: ${{tags || "-"}} | Source report: <code>${{dataset.details.report_path}}</code></p>
            <table>
              <thead>
                <tr>
                  <th>Size</th><th>Mean</th><th>Stddev</th><th>Peak memory</th><th>Min</th><th>Max</th>
                </tr>
              </thead>
              <tbody>${{rows}}</tbody>
            </table>
          </details>`;
      }}).join("");
      applyDetailFilters();
    }}

    function initDetailFilters() {{
      const sizeFilter = document.getElementById("detail-size-filter");
      sizeFilter.innerHTML =
        `<option value="all">All sizes (worst case)</option>` +
        payload.sizes.map((size) => `<option value="${{size}}">Size ${{size}}</option>`).join("");

      ["detail-search", "detail-max-memory", "detail-max-runtime", "detail-size-filter"].forEach((id) => {{
        document.getElementById(id).addEventListener("input", applyDetailFilters);
        document.getElementById(id).addEventListener("change", applyDetailFilters);
      }});

      document.getElementById("detail-clear-filters").addEventListener("click", () => {{
        document.getElementById("detail-search").value = "";
        document.getElementById("detail-max-memory").value = "";
        document.getElementById("detail-max-runtime").value = "";
        document.getElementById("detail-size-filter").value = "all";
        applyDetailFilters();
      }});
    }}

    function refreshAll() {{
      refreshRuntime();
      refreshMemory();
      refreshLoc();
      refreshArtifact();
      refreshBuild();
      renderWinnerTable();
    }}

    renderWarnings();

    [...new Set(payload.datasets.map((dataset) => dataset.lang))].sort().forEach((lang) => {{
      const label = document.createElement("label");
      label.className = "toggle";
      label.innerHTML = `<input type="checkbox" checked> ${{lang}}`;
      label.querySelector("input").addEventListener("change", (event) => {{
        if (event.target.checked) hiddenLangs.delete(lang);
        else hiddenLangs.add(lang);
        refreshAll();
      }});
      document.getElementById("language-controls").appendChild(label);
    }});

    payload.datasets.forEach((dataset) => {{
      const label = document.createElement("label");
      label.className = "toggle";
      label.innerHTML = `<input type="checkbox" checked> ${{dataset.label}}`;
      label.querySelector("input").addEventListener("change", (event) => {{
        if (event.target.checked) hiddenLabels.delete(dataset.label);
        else hiddenLabels.add(dataset.label);
        refreshAll();
      }});
      document.getElementById("implementation-controls").appendChild(label);
    }});

    document.getElementById("build-time-nonzero-only").addEventListener("change", (event) => {{
      buildTimeNonZeroOnly = event.target.checked;
      refreshBuild();
      renderWinnerTable();
    }});

    renderDetails();
    initDetailFilters();
    refreshAll();
  </script>
</body>
</html>
"""


def build_index_markdown(tasks: dict[tuple[str, str], list[Entry]]) -> str:
    lines = [
        "# Benchmark reports",
        "",
        f"Generated at {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Tasks",
        "",
        "| Domain | Task | Implementations | Report |",
        "| --- | --- | --- | --- |",
    ]

    for (domain, test), entries in sorted(tasks.items()):
        rel = f"{domain}/{test}/index.html"
        lines.append(
            f"| {domain} | {test} | {len(entries)} | [{domain}/{test}]({rel}) |"
        )

    lines.append("")
    return "\n".join(lines)


def build_index_html(tasks: dict[tuple[str, str], list[Entry]]) -> str:
    links = []
    for (domain, test), entries in sorted(tasks.items()):
        rel = f"{domain}/{test}/index.html"
        links.append(
            f'<li><a href="{rel}">{html.escape(domain)} / {html.escape(test)}</a> '
            f"({len(entries)} implementations)</li>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Benchmark reports</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 2rem; background: #0f172a; color: #e5e7eb; }}
    a {{ color: #38bdf8; }}
  </style>
</head>
<body>
  <h1>Benchmark reports</h1>
  <p>Generated at {datetime.now(timezone.utc).isoformat()}</p>
  <ul>
    {''.join(links)}
  </ul>
</body>
</html>
"""


def matches_filter(domain: str, test: str, filter_path: str) -> bool:
    if not filter_path:
        return True

    normalized = filter_path.strip("/")
    if normalized.startswith("benchmarks/"):
        normalized = normalized[len("benchmarks/") :]

    parts = Path(normalized).parts
    if len(parts) >= 1 and domain != parts[0]:
        return False
    if len(parts) >= 2 and test != parts[1]:
        return False
    return True


def generate_reports(filters: list[str] | None = None) -> None:
    entries = discover_reports()
    tasks = group_by_task(entries)

    if not tasks:
        print("No benchmark reports found.")
        return

    filter_path = filters[0] if filters else ""
    tasks_to_update = {
        key: value
        for key, value in tasks.items()
        if matches_filter(key[0], key[1], filter_path)
    }

    if filter_path and not tasks_to_update:
        print(f"No reports found for scope: benchmarks/{filter_path.strip('/')}")
        return

    target_tasks = tasks_to_update if filter_path else tasks

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    for (domain, test), task_entries in target_tasks.items():
        task_dir = REPORT_ROOT / domain / test
        task_dir.mkdir(parents=True, exist_ok=True)

        (task_dir / "index.md").write_text(
            build_task_markdown(domain, test, task_entries),
            encoding="utf-8",
        )
        (task_dir / "index.html").write_text(
            build_task_html(domain, test, task_entries),
            encoding="utf-8",
        )

    (REPORT_ROOT / "index.md").write_text(build_index_markdown(tasks), encoding="utf-8")
    (REPORT_ROOT / "index.html").write_text(build_index_html(tasks), encoding="utf-8")

    if filter_path:
        print(
            f"✔ Incrementally updated {len(target_tasks)} task report(s) "
            f"for benchmarks/{filter_path.strip('/')} (index refreshed)"
        )
    else:
        print(f"✔ Generated reports for {len(target_tasks)} task(s) in {REPORT_ROOT}")


if __name__ == "__main__":
    generate_reports(sys.argv[1:] if len(sys.argv) > 1 else None)
