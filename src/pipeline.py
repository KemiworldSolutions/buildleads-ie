"""
End-to-end weekly run:
  1. Discover and fetch council weekly-list files
  2. Extract structured applications via DeepSeek (with optional per-file cap)
  3. Build per-segment digests for the top trade buckets

Usage:
    python -m src.pipeline                    # full run (~€0.70)
    python -m src.pipeline --limit 10         # capped run (~€0.25) — use for testing
    python -m src.pipeline --skip-fetch       # use existing out/raw files
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .digest import build_digest
from .extract import extract_file
from .scraper import fetch_all

TOP_SEGMENTS = [
    "roofing",
    "solar_pv",
    "structural_engineering",
    "architecture",
    "kitchens",
    "windows_glazing",
    "insulation",
    "scaffolding",
]


def run(limit: int | None = None, skip_fetch: bool = False) -> None:
    print("=== STEP 1: fetch council weekly lists ===")
    if skip_fetch:
        print("  (skipping, using existing out/raw files)")
        # rebuild file list from disk
        raw_files: list[tuple[Path, str, str]] = []
        for council_dir in Path("out/raw").glob("*"):
            if not council_dir.is_dir():
                continue
            for f in council_dir.glob("*"):
                fmt = f.suffix.lstrip(".").lower()
                if fmt in ("pdf", "docx", "doc"):
                    raw_files.append((f, council_dir.name, fmt))
    else:
        raw_files = fetch_all()

    if not raw_files:
        print("No raw files available. Aborting.")
        return

    print(f"\n=== STEP 2: extract structured applications ({len(raw_files)} files, limit={limit}) ===")
    out_dir = Path("out/structured")
    out_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    for path, council_code, fmt in raw_files:
        try:
            rows = extract_file(path, council_code, fmt, limit=limit)
        except Exception as e:
            print(f"  [error] {path}: {e}")
            continue
        out_file = out_dir / f"{path.stem}.jsonl"
        with out_file.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        total_rows += len(rows)
        print(f"  [wrote] {out_file} ({len(rows)} rows)")

    print(f"\n  Total extracted: {total_rows} applications")

    print("\n=== STEP 3: build per-segment digests ===")
    for seg in TOP_SEGMENTS:
        build_digest(seg)

    print("\nDone. See out/digests/ for the artifacts.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max entries per file")
    parser.add_argument("--skip-fetch", action="store_true", help="Use existing out/raw files")
    args = parser.parse_args()
    run(limit=args.limit, skip_fetch=args.skip_fetch)
