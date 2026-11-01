"""Download INE tables (hotel occupancy and profitability) through the INE JSON API.

The raw JSON response is saved untouched in data/raw/ine/<name>.json, so the
rest of the pipeline can be rerun without hitting the API again.

Usage:
    python -m etl.download_ine            # all tables in etl/config.py
    python -m etl.download_ine --since 2015
"""
from __future__ import annotations

import argparse
import json
import time

import requests

from etl.config import INE_API, INE_RAW, INE_TABLES


def fetch_table(table_id: int, since_year: int | None = None, retries: int = 3) -> list[dict]:
    """Return every series of an INE table, with variable metadata (tip=AM)."""
    params = {"tip": "AM"}
    if since_year:
        params["date"] = f"{since_year}0101:"
    url = INE_API.format(table_id=table_id)
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=120)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"  attempt {attempt} failed ({exc}); retrying in {wait}s")
            time.sleep(wait)
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=int, default=2010, help="first year to download")
    args = parser.parse_args()

    INE_RAW.mkdir(parents=True, exist_ok=True)
    for name, table_id in INE_TABLES.items():
        print(f"Downloading INE table {table_id} ({name})...")
        series = fetch_table(table_id, since_year=args.since)
        out = INE_RAW / f"{name}.json"
        out.write_text(json.dumps(series, ensure_ascii=False), encoding="utf-8")
        n_points = sum(len(s.get("Data", [])) for s in series)
        print(f"  {len(series)} series, {n_points} data points -> {out.relative_to(INE_RAW.parents[2])}")


if __name__ == "__main__":
    main()
