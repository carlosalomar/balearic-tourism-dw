"""Load the warehouse snapshot and re-aggregate it correctly.

Rates (occupancy, ADR, RevPAR, average stay, spending per day) are never
averaged: the additive components are summed at the requested grain first and
divided afterwards, exactly as the dbt marts do.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"

PRICE_START_YEAR = 2021          # INE IRSH (ADR, RevPAR) starts in January 2021
HIGH_SEASON_MONTHS = [6, 7, 8, 9]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@st.cache_data(show_spinner=False)
def load() -> dict[str, pd.DataFrame]:
    tables = {}
    for path in sorted(DATA_DIR.glob("*.parquet")):
        df = pd.read_parquet(path)
        if "month_start" in df.columns:
            df["month_start"] = pd.to_datetime(df["month_start"])
        tables[path.stem] = df
    if "island_monthly" in tables:
        im = tables["island_monthly"]
        im["month_start"] = pd.to_datetime(im["year_month"] + "-01")
    return tables


def last_month(df: pd.DataFrame, column: str) -> pd.Timestamp:
    return df.loc[df[column].notna(), "month_start"].max()


def complete_years(df: pd.DataFrame, column: str) -> list[int]:
    """Years in which `column` has data for all twelve months (for at least one row)."""
    months = df.loc[df[column].notna()].groupby("year")["month"].nunique()
    return sorted(months[months == 12].index.tolist())


def hotel_rates(components: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Sum hotel components at the `by` grain, then compute the rates.

    ADR and RevPAR only use months with IRSH revenue (2021 onwards), so mixing
    priced and unpriced months never dilutes them.
    """
    c = components.copy()
    priced = c["room_revenue_eur"].notna()
    c["available_room_nights_priced"] = c["available_room_nights"].where(priced)
    sums = c.groupby(by, dropna=False).agg(
        travellers=("travellers", "sum"),
        overnight_stays=("overnight_stays", "sum"),
        overnight_stays_abroad=("overnight_stays_abroad", "sum"),
        overnight_stays_spain=("overnight_stays_spain", "sum"),
        available_room_nights=("available_room_nights", "sum"),
        occupied_room_nights=("occupied_room_nights", "sum"),
        available_bed_nights=("available_bed_nights", "sum"),
        occupied_bed_nights=("occupied_bed_nights", "sum"),
        room_revenue_eur=("room_revenue_eur", lambda s: s.sum(min_count=1)),
        rooms_sold=("rooms_sold", lambda s: s.sum(min_count=1)),
        available_room_nights_priced=("available_room_nights_priced", lambda s: s.sum(min_count=1)),
        months=("month", "nunique"),
        is_provisional=("is_provisional", "max"),
    ).reset_index()
    nz = lambda s: s.where(s > 0)  # noqa: E731
    sums["room_occupancy_rate"] = sums["occupied_room_nights"] / nz(sums["available_room_nights"])
    sums["bed_occupancy_rate"] = sums["occupied_bed_nights"] / nz(sums["available_bed_nights"])
    sums["adr_eur"] = sums["room_revenue_eur"] / nz(sums["rooms_sold"])
    sums["revpar_eur"] = sums["room_revenue_eur"] / nz(sums["available_room_nights_priced"])
    sums["average_stay_nights"] = sums["overnight_stays"] / nz(sums["travellers"])
    sums["share_abroad"] = sums["overnight_stays_abroad"] / nz(sums["overnight_stays"])
    return sums


def filter_islands(df: pd.DataFrame, island: str) -> pd.DataFrame:
    """'All islands' keeps every row, Unallocated included, so totals match the province."""
    if island == "All islands":
        return df
    return df[df["island_name"] == island]
