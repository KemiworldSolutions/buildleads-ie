"""
Group extracted applications into per-trade buckets for digest building.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def load_all_structured() -> list[dict]:
    rows: list[dict] = []
    for p in Path("out/structured").glob("*.jsonl"):
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def bucket_by_trade(rows: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        for t in r.get("trades_relevant", []):
            buckets[t].append(r)
        for p in r.get("professionals_relevant", []):
            buckets[p].append(r)
    return buckets
