"""Download monthly passengers for the three Balearic airports.

Source: Eurostat dataset avia_paoa (air passenger transport by reporting
airport), which republishes the traffic figures that AENA reports. It has a
stable JSON API, so the download is fully scripted.

Saves data/raw/airports/avia_paoa.json (raw) for etl/transform.py.

Usage:
    python -m etl.download_airports
"""
from __future__ import annotations

import json

import requests

from etl.config import AIRPORT_RAW, AIRPORTS, EUROSTAT_API


def fetch_passengers(since: str = "2010-01") -> dict:
    params = [
        ("format", "JSON"),
        ("lang", "EN"),
        ("freq", "M"),
        ("unit", "PAS"),
        ("tra_meas", "PAS_CRD"),      # passengers carried (arrivals + departures)
        ("tra_meas", "PAS_CRD_ARR"),  # arriving passengers only
        ("schedule", "TOTAL"),        # scheduled + charter flights
        ("tra_cov", "TOTAL"),
        ("tra_cov", "NAT"),           # domestic flights (proxy for Spanish market)
        ("tra_cov", "INTL"),          # international flights
        ("sinceTimePeriod", since),
    ]
    params += [("rep_airp", code) for code in AIRPORTS]
    resp = requests.get(EUROSTAT_API, params=params, timeout=120)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    AIRPORT_RAW.mkdir(parents=True, exist_ok=True)
    data = fetch_passengers()
    out = AIRPORT_RAW / "avia_paoa.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    print(f"Saved {len(data.get('value', {}))} observations -> {out}")


if __name__ == "__main__":
    main()
