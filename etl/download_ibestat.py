"""Download FRONTUR / EGATUR datasets from the IBESTAT eDatos (Metamac) API.

Each dataset has many published versions (1.0, 1.1, ... 1.32); the API lists
them and this script picks the highest one, comparing versions numerically
(a plain string sort would rank "1.9" above "1.32").

Usage:
    python -m etl.download_ibestat
"""
from __future__ import annotations

import json

import requests

from etl.config import IBESTAT_API, IBESTAT_DATASETS, IBESTAT_RAW

HEADERS = {"Accept": "application/json"}


def latest_version(dataset_id: str) -> str:
    resp = requests.get(
        IBESTAT_API.format(dataset_id=dataset_id),
        params={"limit": 1000},  # the version list is paginated (25 by default)
        headers=HEADERS,
        timeout=60,
    )
    resp.raise_for_status()
    versions = [d["selfLink"]["href"].rsplit("/", 1)[-1] for d in resp.json()["dataset"]]
    return max(versions, key=lambda v: tuple(int(x) for x in v.split(".")))


def fetch_dataset(dataset_id: str) -> dict:
    version = latest_version(dataset_id)
    url = IBESTAT_API.format(dataset_id=dataset_id) + f"/{version}"
    resp = requests.get(url, headers=HEADERS, timeout=180)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    IBESTAT_RAW.mkdir(parents=True, exist_ok=True)
    for name, dataset_id in IBESTAT_DATASETS.items():
        print(f"Downloading IBESTAT {dataset_id} ({name})...")
        data = fetch_dataset(dataset_id)
        out = IBESTAT_RAW / f"{name}.json"
        out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        version = data["urn"].rsplit("(", 1)[-1].rstrip(")")
        print(f"  version {version} -> {out.name}")


if __name__ == "__main__":
    main()
