"""Export the tables the dashboard needs from the DuckDB warehouse to Parquet.

The warehouse file (data/balearic_tourism.duckdb) is not committed, so the
deployed app reads this small snapshot instead. Every query reads only from the
`core` and `analytics` schemas built by dbt.

    python dashboard/export_data.py            # after `dbt build`
"""

import os
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = Path(os.environ.get("DUCKDB_PATH", REPO_ROOT / "data" / "balearic_tourism.duckdb"))
OUT_DIR = Path(__file__).resolve().parent / "data"

QUERIES = {
    # Drill-across mart: one row per island x month, all five facts.
    "island_monthly": "select * from analytics.mart_island_monthly",
    # Additive hotel components per destination x month, so that rates can be
    # re-aggregated correctly (sum the components, then divide) at any level.
    "hotel_components": """
        with demand as (
            select f.date_key, f.destination_key,
                   sum(f.travellers) as travellers,
                   sum(f.overnight_stays) as overnight_stays,
                   sum(f.overnight_stays) filter (where r.residence_code = 'SPAIN') as overnight_stays_spain,
                   sum(f.overnight_stays) filter (where r.residence_code = 'ABROAD') as overnight_stays_abroad,
                   bool_or(f.is_provisional) as is_provisional
            from core.fact_hotel_demand as f
            inner join core.dim_residence as r using (residence_key)
            group by all
        ),

        -- full join: Unallocated destination rows exist only on the demand side
        components as (
            select
                coalesce(p.date_key, demand.date_key) as date_key,
                coalesce(p.destination_key, demand.destination_key) as destination_key,
                p.establishments, p.bed_places, p.rooms,
                p.available_bed_nights, p.occupied_bed_nights,
                p.available_room_nights, p.occupied_room_nights,
                p.room_revenue_eur, p.rooms_sold,
                demand.travellers, demand.overnight_stays,
                demand.overnight_stays_spain, demand.overnight_stays_abroad,
                coalesce(p.is_provisional, demand.is_provisional) as is_provisional
            from core.fact_hotel_performance as p
            full join demand using (date_key, destination_key)
        )

        select
            d.date_key, d.month_start, d.year_month, d.year, d.month,
            d.month_short_name, d.season, d.is_covid_period,
            dest.destination_name, dest.island_name,
            c.* exclude (date_key, destination_key)
        from components as c
        inner join core.dim_date as d using (date_key)
        inner join core.dim_destination as dest using (destination_key)
        order by d.date_key, dest.destination_name
    """,
    # FRONTUR tourist arrivals by island x source market x month.
    "tourist_markets": """
        select d.date_key, d.month_start, d.year_month, d.year, d.month, d.season,
               i.island_name, o.origin_code, o.market_name, o.residence_name,
               f.tourists
        from core.fact_tourist_arrivals as f
        inner join core.dim_date as d using (date_key)
        inner join core.dim_island as i using (island_key)
        inner join core.dim_origin as o using (origin_key)
        order by date_key, island_name, origin_code
    """,
    # EGATUR spending by island x (coarser) market x month.
    "spending_markets": """
        select d.date_key, d.month_start, d.year_month, d.year, d.month, d.season,
               i.island_name, m.egatur_market_code, m.egatur_market_name,
               f.spending_eur, f.tourist_days
        from core.fact_tourist_spending as f
        inner join core.dim_date as d using (date_key)
        inner join core.dim_island as i using (island_key)
        inner join core.dim_egatur_market as m using (egatur_market_key)
        order by date_key, island_name, egatur_market_code
    """,
}


def main() -> None:
    if not WAREHOUSE.exists():
        raise SystemExit(f"Warehouse not found at {WAREHOUSE}. Run `python -m etl.load_raw` and `dbt build` first.")
    OUT_DIR.mkdir(exist_ok=True)
    with duckdb.connect(str(WAREHOUSE), read_only=True) as con:
        for name, sql in QUERIES.items():
            path = OUT_DIR / f"{name}.parquet"
            con.sql(sql).write_parquet(str(path), compression="zstd")
            rows = con.execute(f"select count(*) from read_parquet('{path}')").fetchall()[0][0]
            print(f"{name:<18} {rows:>6} rows -> {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
