"""
Fetch raw weekly planning lists from each council using live discovery.

Uses src.sources.discover_all() to get the list of current-week files
across all 4 councils, then downloads each one to out/raw/{council}/.
"""

from __future__ import annotations

from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .sources import discover_all

RAW_DIR = Path("out/raw")
HEADERS = {"User-Agent": "PlanRadar/0.1 (+contact: you@example.ie)"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _download(url: str) -> bytes:
    with httpx.Client(timeout=60, follow_redirects=True, headers=HEADERS) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def fetch_all() -> list[tuple[Path, str, str]]:
    """Returns a list of (local_path, council_code, format)."""
    files = discover_all()
    results: list[tuple[Path, str, str]] = []
    for f in files:
        out_dir = RAW_DIR / f.council_code
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f.filename
        try:
            print(f"[fetch] {f.council_code} <- {f.url}")
            data = _download(f.url)
            out_path.write_bytes(data)
            print(f"[saved] {out_path} ({len(data):,} bytes)")
            results.append((out_path, f.council_code, f.format))
        except Exception as e:
            print(f"[error] {f.council_code} {f.filename}: {e}")
    return results


if __name__ == "__main__":
    fetch_all()
