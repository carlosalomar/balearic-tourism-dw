"""Flatten an IBESTAT eDatos (Metamac) dataset into a tidy DataFrame."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd


def _label(value: dict, lang: str) -> str:
    texts = value["name"]["text"]
    return next((t["value"] for t in texts if t["lang"] == lang), texts[0]["value"])


def load_metamac(path: str | Path, lang: str = "es") -> pd.DataFrame:
    """One row per observation: <dim> code and <dim>_label per dimension, plus value.

    Metamac returns observations as one ' | '-separated string in row-major
    order over the dimensions listed in metadata.dimensions (data.dimensions
    gives the order of codes for each one). Missing values are empty strings.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    meta_dims = data["metadata"]["dimensions"]["dimension"]
    labels = {
        d["id"]: {v["id"]: _label(v, lang) for v in d["dimensionValues"]["value"]}
        for d in meta_dims
    }
    order = [d["dimensionId"] for d in data["data"]["dimensions"]["dimension"]]
    codes = {
        d["dimensionId"]: [
            r["code"] for r in sorted(d["representations"]["representation"], key=lambda r: r["index"])
        ]
        for d in data["data"]["dimensions"]["dimension"]
    }
    values = data["data"]["observations"].split(" | ")
    rows = []
    for combo, raw in zip(itertools.product(*(codes[d] for d in order)), values):
        row = {}
        for dim, code in zip(order, combo):
            row[dim] = code
            row[f"{dim}_label"] = labels[dim].get(code, code)
        row["value"] = raw.strip() or None
        rows.append(row)
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df
