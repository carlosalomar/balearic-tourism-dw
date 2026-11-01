"""Flatten a Eurostat JSON-stat 2.0 response into a tidy DataFrame."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd


def load_jsonstat(path: str | Path) -> pd.DataFrame:
    """One row per observation, one column per dimension code, plus `value`.

    JSON-stat stores values in a flat dict keyed by the row-major position in
    the cube defined by `id` (dimension order) and `size` (categories per dim).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    dims = data["id"]
    categories = []
    for dim in dims:
        index = data["dimension"][dim]["category"]["index"]
        categories.append(sorted(index, key=index.get))
    values = data.get("value", {})
    rows = []
    for pos, combo in enumerate(itertools.product(*categories)):
        value = values.get(str(pos))
        if value is not None:
            rows.append((*combo, value))
    return pd.DataFrame(rows, columns=[*dims, "value"])
