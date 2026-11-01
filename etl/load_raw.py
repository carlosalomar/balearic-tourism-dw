"""Load the downloaded source files into the `raw` schema of the DuckDB warehouse.

This is the "EL" step: each JSON file is flattened by its parser (INE Tempus3,
Eurostat JSON-stat, IBESTAT Metamac) and written untouched otherwise, with
source labels kept in Spanish. Renaming, filtering and typing happen in the dbt
staging models.

Usage:
    python -m etl.load_raw                    # -> data/balearic_tourism.duckdb
    DUCKDB_PATH=/tmp/dw.duckdb python -m etl.load_raw
"""
from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd

from etl.config import AIRPORT_RAW, IBESTAT_RAW, INE_RAW, ROOT
from etl.eurostat_parse import load_jsonstat
from etl.ibestat_parse import load_metamac
from etl.ine_parse import balearic_only, load_ine_json

DEFAULT_DB = ROOT / "data" / "balearic_tourism.duckdb"


def snake(name: str) -> str:
    """'ZONAS TURÍSTICAS' -> 'zonas_turisticas'."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9a-z]+", "_", ascii_name.lower()).strip("_")


def ine(name: str) -> pd.DataFrame:
    return balearic_only(load_ine_json(INE_RAW / f"{name}.json"))


def sources() -> dict[str, pd.DataFrame]:
    """raw table name -> flattened DataFrame."""
    return {
        "ine_eoh_zone_demand": ine("eoh_zone_travellers_nights"),
        "ine_eoh_zone_supply": ine("eoh_zone_supply_occupancy"),
        "ine_eoh_province_demand": ine("eoh_province_travellers_nights"),
        "ine_irsh_zone_adr": ine("irsh_zone_adr"),
        "ine_irsh_zone_revpar": ine("irsh_zone_revpar"),
        "eurostat_avia_paoa": load_jsonstat(AIRPORT_RAW / "avia_paoa.json"),
        "ibestat_frontur_tourists": load_metamac(IBESTAT_RAW / "frontur_tourists_island_residence.json"),
        "ibestat_egatur_spending": load_metamac(IBESTAT_RAW / "egatur_spending_island_residence.json"),
        "ibestat_egatur_nights": load_metamac(IBESTAT_RAW / "egatur_nights_island_residence.json"),
    }


def main() -> None:
    db_path = Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("create schema if not exists raw")
    for table, df in sources().items():
        df = df.rename(columns=snake)
        con.register("df", df)
        con.execute(f"create or replace table raw.{table} as select * from df")
        con.unregister("df")
        print(f"raw.{table:<28} {len(df):>7,} rows")
    con.close()
    print(f"Warehouse: {db_path}")


if __name__ == "__main__":
    main()
