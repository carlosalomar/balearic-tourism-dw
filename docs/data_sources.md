# Data sources and granularity

Before designing the schema, each public source was downloaded and checked for
the level of detail it actually provides for the Balearic Islands. The checks
are reproducible in [`notebooks/01_explore_sources.ipynb`](../notebooks/01_explore_sources.ipynb).

| Source | Script | Grain | Coverage |
|---|---|---|---|
| INE EOH (hotel occupancy survey) | `etl/download_ine.py` | tourist zone x residence (Spain / abroad) x month | 2010-01 → 2026-09 |
| INE IRSH (hotel profitability) | `etl/download_ine.py` | tourist zone x month | 2021-01 → 2026-09 |
| Eurostat `avia_paoa` (AENA traffic) | `etl/download_airports.py` | airport x domestic / international x month | 2010-01 → 2026-06 |
| IBESTAT FRONTUR / EGATUR | `etl/download_ibestat.py` | island x country of residence x month | 2015-10 → 2026-08 |

## INE: Hotel Occupancy Survey (EOH), monthly

Tempus3 API: `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/<id>?tip=AM`.

| Table | Content | Balearic detail |
|---|---|---|
| 2039 | Travellers and overnight stays | Tourist zone x residence (Spain / abroad) |
| 2013 | Establishments, bed places, rooms, occupancy rates, staff | Tourist zone |
| 2074 | Travellers and overnight stays | Province (Illes Balears) x residence |
| 2038 | Travellers and overnight stays by country of residence | **National only** (0 Balearic rows) |

Balearic tourist zones: *Isla de Mallorca*, *Palma - Calvià*, *Isla de Menorca*,
*Islas de Ibiza-Formentera*.

**Isla de Mallorca includes Palma - Calvià.** In all 150 months where the three
islands are published, Mallorca + Menorca + Ibiza-Formentera equals the
province total within ±2 (independent rounding of the two tables); adding
Palma - Calvià overshoots by 26-77 %. Palma -
Calvià is a sub-zone of Mallorca, not a sibling.

**Winter suppression.** In 49 of 201 months at least one island is not
published because too few hotels are open (Menorca is missing in 88 % of
Decembers, Ibiza-Formentera in 75 %). The province total is always published.

## INE: Hotel Sector Profitability Indicators (IRSH), monthly

| Table | Content | Balearic detail |
|---|---|---|
| 46297 | ADR (average daily rate) | Tourist zone, since 2021 |
| 46300 | RevPAR (revenue per available room) | Tourist zone, since 2021 |

RevPAR / ADR reproduces the EOH room occupancy rate within about 1 percentage
point (median), so both surveys can be combined. The gap stays under 5 points in
every non-provisional high-season month (dbt test) but can reach 20 points in
winter, when few hotels are open.

## Airports: monthly passengers

AENA has no API, but Eurostat `avia_paoa` republishes its figures (Palma 2024:
33.3 M passengers, as reported by AENA). The download keeps
`schedule=TOTAL`, both passengers carried and arriving passengers, and the
domestic / international split (`tra_cov`). Reporting airports: `ES_LEPA`
Palma (PMI), `ES_LEIB` Ibiza (IBZ), `ES_LEMH` Menorca (MAH). Eurostat lags
AENA by about three months.

## IBESTAT: FRONTUR and EGATUR, monthly

IBESTAT exposes its data bank through the eDatos (Metamac) API:
`https://ibestat.es/edatos/apis/statistical-resources/v1.0/datasets/IBESTAT/<id>/<version>`.
Each dataset has many versions; the script picks the highest one numerically.

| Dataset | Content | Detail |
|---|---|---|
| 000058A_000002 | FRONTUR tourists | Island x residence: Germany, UK, France, Italy, Nordics, Benelux, other abroad, Spain (excl. Balearics) |
| 000059A_000007 | EGATUR spending (total, per person, per day) | Island x residence: Germany, UK, other abroad, Spain |
| 000059A_000011 | EGATUR tourist nights and average stay | Island x Spain / abroad |

Islands and markets add up exactly to their totals. Small cells are
suppressed (30 % of Menorca cells, 12 % of Ibiza-Formentera).

**Caveat:** IBESTAT's *Spain* excludes Balearic residents, while INE's
*Residentes en España* includes them. The two only meet at the
Spain / abroad level, and the dashboard labels the difference.

## Decisions for the model

1. **Destination leaves are additive.** `dim_destination` holds *Palma - Calvià*,
   *Rest of Mallorca* (derived: Isla de Mallorca − Palma - Calvià), *Menorca*,
   *Ibiza-Formentera* and *Unallocated* (derived: province − published
   islands, only in the 51 months where an island is suppressed, including
   May-June 2020 when no zone was published). Demand then sums to the Balearic
   total in every month (±3 rounding, enforced by a dbt test).
2. **Two hotel facts.** Travellers and nights come split by residence;
   supply, occupancy and prices do not. They become `fact_hotel_demand` and
   `fact_hotel_performance`.
3. **Store components, not rates.** Occupancy, ADR and RevPAR are not
   additive, so the performance fact stores available bed-nights and
   room-nights, occupied room-nights, room revenue (RevPAR x available
   room-nights) and rooms sold (revenue / ADR). Rates are recomputed in the
   marts, which also gives them for the derived *Rest of Mallorca*.
4. **Source markets come from FRONTUR.** `fact_tourist_arrivals` is a core
   fact at island x market grain. EGATUR spending uses fewer markets, so it
   gets its own `fact_tourist_spending` at the coarser grain of
   `dim_egatur_market`, a rollup of `dim_origin`. Suppressed IBESTAT cells go
   to an *Abroad (unallocated)* member so markets add up to island totals.
   Tourist days are derived as spending / spending per person-day and match
   EGATUR's published tourist nights within 0.2 %.
5. **Shrunken rollup dimensions.** `dim_island` rolls up `dim_destination`;
   `dim_egatur_market` and `dim_residence` roll up `dim_origin`, so hotel, airport and FRONTUR
   facts can be compared at island and Spain / abroad level (drill-across).
6. **Dropped:** hotel category and country at Balearic level in the EOH
   (national only).
7. **Time window.** The dashboard defaults to 2016 onwards (all sources
   overlap); price analysis starts in 2021.
