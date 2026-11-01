"""Flatten raw INE Tempus3 JSON (downloaded with tip=AM) into a tidy DataFrame."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

# Tempus3 series names use different spellings for the islands depending on the table.
BALEARIC_PATTERN = r"Baleares \(Illes\)|Balears, Illes"


def load_ine_json(path: str | Path) -> pd.DataFrame:
    """One row per series and period.

    Columns: series_code, series_name, unit, one column per INE variable found in
    the series metadata (e.g. 'ZONAS TURÍSTICAS', 'RESIDENCIA/ORIGEN',
    'Concepto turístico'), year, month, period, data_status
    (Definitivo / Provisional), value.
    """
    series = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for s in series:
        meta = {
            (m.get("T3_Variable") or m.get("Variable", {}).get("Nombre")): m.get("Nombre")
            for m in s.get("MetaData", [])
        }
        for point in s.get("Data", []):
            period = point.get("T3_Periodo") or ""
            match = re.fullmatch(r"M(\d{2})", period)
            rows.append(
                {
                    "series_code": s.get("COD"),
                    "series_name": s.get("Nombre"),
                    "unit": s.get("T3_Unidad"),
                    **meta,
                    "year": point.get("Anyo"),
                    "month": int(match.group(1)) if match else None,
                    "period": period,
                    "data_status": point.get("T3_TipoDato"),
                    "value": point.get("Valor"),
                }
            )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def balearic_only(df: pd.DataFrame, pattern: str = BALEARIC_PATTERN) -> pd.DataFrame:
    """Keep rows whose series name mentions the Balearic Islands or one of their zones."""
    return df[df["series_name"].str.contains(pattern, case=False, na=False, regex=True)].copy()
