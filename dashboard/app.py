"""Balearic Tourism dashboard.

Business question: how do hotel demand, occupancy and prices behave in the
Balearic Islands by island, season and the tourist's country of origin?

Run from the repository root:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import charts  # noqa: E402
from charts import ISLANDS, UNALLOCATED  # noqa: E402
from data import (  # noqa: E402
    HIGH_SEASON_MONTHS, MONTHS, PRICE_START_YEAR, complete_years, filter_islands, hotel_rates, last_month, load,
)

st.set_page_config(page_title="Balearic Tourism", page_icon="🏝️", layout="wide")


def theme_mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except AttributeError:  # older Streamlit without st.context.theme
        return "light"


MODE = theme_mode()
COLORS = charts.island_colors(MODE)
PLOT = dict(theme=None, config={"displayModeBar": False})

tables = load()
if not tables:
    st.error("No data found in dashboard/data/. Run `python dashboard/export_data.py` after `dbt build`.")
    st.stop()

hotel = tables["hotel_components"]
monthly = tables["island_monthly"]
markets = tables["tourist_markets"]
spending = tables["spending_markets"]

hotel_last = last_month(hotel, "overnight_stays")
hotel_years = complete_years(hotel, "overnight_stays")  # province total: Unallocated fills suppressed months


def fmt_month(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def people(x: float | None) -> str:
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x / 1e6:.1f} M" if x >= 1e6 else f"{x / 1e3:,.0f}k"


def pct(x: float | None, digits: int = 1) -> str:
    return "n/a" if x is None or pd.isna(x) else f"{x:.{digits}%}"


# --------------------------------------------------------------------------- header
st.title("Balearic Islands hotel tourism")
st.markdown(
    "How do **hotel demand, occupancy and prices** behave by **island, season and country of origin**? "
    "Built on a DuckDB + dbt star schema fed by INE, Eurostat and IBESTAT open data."
)
st.caption(
    f"Data through {fmt_month(hotel_last)} for hotels (INE), "
    f"{fmt_month(last_month(markets, 'tourists'))} for tourist arrivals (FRONTUR), "
    f"{fmt_month(last_month(monthly, 'airport_passengers'))} for airports (Eurostat). "
    "Recent months are provisional."
)

# Filters live in one row above the content and apply to every tab.
f1, f2, _ = st.columns([3, 1.2, 2])
with f1:
    island = st.segmented_control("Island", ["All islands", *ISLANDS], default="All islands",
                                  help="'All islands' includes hotel demand INE did not publish by island (Unallocated).")
    island = island or "All islands"
year_options = sorted(hotel["year"].unique(), reverse=True)
partial_year = hotel_last.year if hotel_last.month < 12 else None
with f2:
    year = st.selectbox(
        "Year", year_options, index=year_options.index(max(hotel_years)),
        format_func=lambda y: f"{y} (to {hotel_last.strftime('%b')})" if y == partial_year else str(y),
    )

tab_overview, tab_season, tab_prices, tab_markets, tab_air, tab_data = st.tabs(
    ["Overview", "Seasonality", "Prices & occupancy", "Source markets", "Airports vs hotels", "Data & method"]
)

hotel_sel = filter_islands(hotel, island)
markets_sel = filter_islands(markets, island)
scope_label = "the Balearic Islands" if island == "All islands" else island

# --------------------------------------------------------------------------- overview
with tab_overview:
    # Compare the selected year with the same months of the previous year, so a
    # partial year or a winter month INE suppressed never fakes a change.
    months_y = set(hotel_sel.loc[(hotel_sel["year"] == year) & hotel_sel["overnight_stays"].notna(), "month"])
    months_p = set(hotel_sel.loc[(hotel_sel["year"] == year - 1) & hotel_sel["overnight_stays"].notna(), "month"])
    common = sorted(months_y & months_p) if months_p else sorted(months_y)
    span = hotel_sel[hotel_sel["month"].isin(common) & hotel_sel["year"].isin([year, year - 1])]
    k = hotel_rates(span, ["year"]).set_index("year")
    cur = k.loc[year] if year in k.index else None
    prev = k.loc[year - 1] if (year - 1) in k.index else None

    # FRONTUR is published on its own calendar: compare only months it has in both years
    t_months = [m for m in common
                if all(((markets_sel["year"] == yy) & (markets_sel["month"] == m)).any() for yy in (year, year - 1))]
    t = markets_sel[markets_sel["month"].isin(t_months)].groupby("year")["tourists"].sum(min_count=1)
    if len(common) == 12:
        period = f"{year}, compared with {year - 1}"
    else:
        period = f"{MONTHS[common[0] - 1]}–{MONTHS[common[-1] - 1]} {year} (months published in both years), compared with {year - 1}"
    st.subheader(f"Key figures for {scope_label}")
    st.caption(period)

    def delta(field, kind):
        if prev is None or cur is None or pd.isna(prev[field]) or pd.isna(cur[field]):
            return None
        if kind == "rate":
            return f"{(cur[field] - prev[field]) * 100:+.1f} pp"
        return f"{cur[field] / prev[field] - 1:+.1%}"

    c = st.columns(6)
    priced = year >= PRICE_START_YEAR
    c[0].metric("Hotel overnight stays", people(cur["overnight_stays"]) if cur is not None else "n/a",
                delta("overnight_stays", "abs"), border=True)
    c[1].metric("Room occupancy", pct(cur["room_occupancy_rate"]) if cur is not None else "n/a",
                delta("room_occupancy_rate", "rate"), border=True,
                help="Occupied / available room-nights in published zones.")
    c[2].metric("ADR", f"€{cur['adr_eur']:.0f}" if priced and cur is not None and pd.notna(cur["adr_eur"]) else "n/a",
                delta("adr_eur", "abs") if priced else None, border=True,
                help="Average daily rate: room revenue / rooms sold. INE publishes it from 2021.")
    c[3].metric("RevPAR", f"€{cur['revpar_eur']:.0f}" if priced and cur is not None and pd.notna(cur["revpar_eur"]) else "n/a",
                delta("revpar_eur", "abs") if priced else None, border=True,
                help="Revenue per available room: room revenue / available room-nights. From 2021.")
    c[4].metric("Average stay", f"{cur['average_stay_nights']:.1f} nights" if cur is not None else "n/a",
                delta("average_stay_nights", "abs"), border=True)
    tourists_now, tourists_prev = t.get(year), t.get(year - 1)
    c[5].metric("Tourists (FRONTUR)", people(tourists_now),
                f"{tourists_now / tourists_prev - 1:+.1%}" if pd.notna(tourists_now) and pd.notna(tourists_prev) else None,
                border=True, help="All tourists arriving, any accommodation. Available from Oct 2015.")
    if t_months and len(t_months) < len(common):
        c[5].caption(f"FRONTUR: {MONTHS[t_months[0] - 1]}–{MONTHS[t_months[-1] - 1]} only")
    if not priced:
        st.caption(f"ADR and RevPAR come from INE's IRSH survey, which starts in {PRICE_START_YEAR}.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Hotel overnight stays per year**")
        yearly = hotel_rates(hotel_sel[hotel_sel["year"].isin(hotel_years)], ["year", "island_name"])
        order = [*ISLANDS, UNALLOCATED] if island == "All islands" else [island]
        fig = charts.stacked_columns(yearly, "year", "overnight_stays", "island_name", order, COLORS, MODE,
                                     ",.0f", y_format="~s", height=340)
        st.plotly_chart(fig, **PLOT)
        if island == "All islands":
            st.caption("Complete years only. Grey = nights INE did not publish by island (winter months, May–Jun 2020): "
                       "they belong to the province total but to no single island.")
        else:
            st.caption("Complete years only. Months INE did not publish for this island are not included, "
                       "so years with suppressed winter months (and 2020) are understated.")
    with right:
        st.markdown("**Room occupancy, high season (Jun–Sep)**")
        hs = hotel_rates(hotel[hotel["month"].isin(HIGH_SEASON_MONTHS) & hotel["year"].isin(hotel_years)
                               & hotel["island_name"].isin(ISLANDS)], ["year", "island_name"])
        hs = hs[(hs["year"] != 2020) & (hs["year"] >= 2015)]  # rooms from 2015; no comparable summer in 2020
        fig = charts.lines(hs, "year", "room_occupancy_rate", "island_name",
                           ISLANDS if island == "All islands" else [island], COLORS, MODE, ".1%",
                           y_format=".0%", height=340, markers=True, zero_base=False)
        st.plotly_chart(fig, **PLOT)
        st.caption("Room supply is published from 2015. 2020 left out: hotels were closed for most of the summer.")

# --------------------------------------------------------------------------- seasonality
with tab_season:
    st.subheader("How seasonal is each island?")
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Share of the year's hotel nights by month, {year}**")
        y_rows = hotel_rates(hotel[(hotel["year"] == year) & hotel["island_name"].isin(ISLANDS)], ["island_name", "month"])
        y_rows["share"] = y_rows["overnight_stays"] / y_rows.groupby("island_name")["overnight_stays"].transform("sum")
        full = pd.MultiIndex.from_product([ISLANDS, range(1, 13)], names=["island_name", "month"]).to_frame(index=False)
        y_rows = full.merge(y_rows, how="left")
        fig = charts.lines(y_rows, "month", "share", "island_name",
                           ISLANDS if island == "All islands" else [island], COLORS, MODE, ".1%",
                           y_format=".0%", height=360, markers=True, end_labels=False)
        fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=MONTHS, range=[0.6, 12.4])
        st.plotly_chart(fig, **PLOT)
        st.caption("Gaps are months INE did not publish for that island (too few hotels open). "
                   "Shares are of the published months, so the smaller islands' peaks are slightly overstated.")
    with right:
        st.markdown("**High-season share: Jun–Sep nights as % of the year**")
        yr = hotel_rates(hotel[hotel["year"].isin(hotel_years) & hotel["island_name"].isin(ISLANDS)],
                         ["year", "island_name"])
        hi = hotel_rates(hotel[hotel["year"].isin(hotel_years) & hotel["island_name"].isin(ISLANDS)
                               & hotel["month"].isin(HIGH_SEASON_MONTHS)], ["year", "island_name"])
        yr = yr.merge(hi[["year", "island_name", "overnight_stays"]], on=["year", "island_name"], suffixes=("", "_high"))
        yr["high_share"] = yr["overnight_stays_high"] / yr["overnight_stays"]
        yr = yr[yr["year"] != 2020]
        fig = charts.lines(yr, "year", "high_share", "island_name",
                           ISLANDS if island == "All islands" else [island], COLORS, MODE, ".1%",
                           y_format=".0%", height=360, markers=True, zero_base=False)
        st.plotly_chart(fig, **PLOT)
        st.caption("A falling line means the season is stretching into spring and autumn. 2020 left out; "
                   "the 2021 peak reflects hotels reopening late, in June.")

    st.markdown(f"**Room occupancy by month and year, {scope_label}**")
    hm = hotel_rates(hotel_sel[hotel_sel["island_name"].isin(ISLANDS)], ["year", "month"])
    hm["month_label"] = hm["month"].map(lambda m: MONTHS[m - 1])
    hm = hm[hm["available_room_nights"] > 0]
    fig = charts.heatmap(hm, "month_label", "year", "room_occupancy_rate", MODE, ".1%", MONTHS,
                         sorted(hm["year"].unique()), height=440, colorbar_format=".0%")
    st.plotly_chart(fig, **PLOT)
    st.caption("Empty cells: no hotel supply published (closures in spring 2020, suppressed winter months).")

# --------------------------------------------------------------------------- prices
with tab_prices:
    st.subheader("Do prices rise faster than occupancy?")
    st.caption(f"ADR and RevPAR exist only from January {PRICE_START_YEAR} (INE hotel profitability survey, IRSH).")
    show = ISLANDS if island == "All islands" else [island]
    pm = hotel_rates(hotel[(hotel["year"] >= PRICE_START_YEAR) & hotel["island_name"].isin(show)],
                     ["month_start", "island_name"])
    a, b = st.columns(2)
    with a:
        st.markdown("**ADR: average daily rate (€ per room sold)**")
        fig = charts.lines(pm, "month_start", "adr_eur", "island_name", show, COLORS, MODE, "€,.0f", height=320)
        st.plotly_chart(fig, **PLOT)
    with b:
        st.markdown("**RevPAR: revenue per available room (€)**")
        fig = charts.lines(pm, "month_start", "revpar_eur", "island_name", show, COLORS, MODE, "€,.0f", height=320)
        st.plotly_chart(fig, **PLOT)
    st.markdown("**Room occupancy**")
    fig = charts.lines(pm, "month_start", "room_occupancy_rate", "island_name", show, COLORS, MODE, ".1%",
                       y_format=".0%", height=300)
    st.plotly_chart(fig, **PLOT)

    st.markdown("**Summer price vs summer occupancy, indexed (Jun–Sep 2022 = 100)**")
    base_year = 2022
    idx_years = [y for y in sorted(hotel["year"].unique()) if y >= base_year]
    sm = hotel_rates(hotel[hotel["year"].isin(idx_years) & hotel["month"].isin(HIGH_SEASON_MONTHS)
                           & hotel["island_name"].isin(show)], ["year", "island_name"])
    sm = sm[sm["months"] == len(HIGH_SEASON_MONTHS)]
    long = []
    for measure, label in [("adr_eur", "ADR"), ("room_occupancy_rate", "Room occupancy")]:
        base = sm[sm["year"] == base_year].set_index("island_name")[measure]
        tmp = sm[["year", "island_name"]].copy()
        tmp["index"] = sm[measure].values / sm["island_name"].map(base).values * 100
        tmp["measure"] = label
        long.append(tmp)
    long = pd.concat(long)
    measure_colors = {"ADR": charts.THEMES[MODE]["series"][0], "Room occupancy": charts.THEMES[MODE]["series"][1]}
    fig = charts.small_multiples(long, "year", "index", "island_name", show, MODE, ".0f", cols=len(show),
                                 height_per_row=260, series="measure", series_order=["ADR", "Room occupancy"],
                                 series_colors=measure_colors)
    fig.update_yaxes(rangemode="normal")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, **PLOT)
    st.caption("2021 is not used as the base: it was a recovery year with capacity limits. "
               "When the blue line climbs and the orange one stays flat, revenue growth is coming from price, not volume.")

    st.markdown("**Every island-month since 2022: occupancy against ADR**")
    sc = hotel_rates(hotel[(hotel["year"] >= base_year) & hotel["island_name"].isin(show)],
                     ["year_month", "island_name"])
    fig = charts.scatter(sc, "room_occupancy_rate", "adr_eur", "island_name", show, COLORS, MODE,
                         ".0%", "€,.0f", "year_month", x_title="Room occupancy", y_title="ADR", height=400)
    st.plotly_chart(fig, **PLOT)
    st.caption("Prices climb steeply once occupancy passes ~85 %: the peak months carry the year's pricing power.")

# --------------------------------------------------------------------------- markets
with tab_markets:
    st.subheader(f"Where do {scope_label}' tourists come from?" if island == "All islands"
                 else f"Where do {island}'s tourists come from?")
    m_years = complete_years(markets, "tourists")
    m_year_default = year if year in m_years else max(m_years)
    c1, c2, _ = st.columns([1, 1, 3])
    m_year = c1.selectbox("Year", m_years, index=m_years.index(m_year_default), key="m_year")
    base_options = [y for y in m_years if y < m_year] or m_years
    m_base = c2.selectbox("Compared with", base_options,
                          index=base_options.index(2019) if 2019 in base_options else 0, key="m_base")
    by_market = markets_sel.groupby(["year", "market_name"], as_index=False)["tourists"].sum()
    cur_m = by_market[by_market["year"] == m_year].set_index("market_name")["tourists"]
    base_m = by_market[by_market["year"] == m_base].set_index("market_name")["tourists"]
    comp = pd.DataFrame({"tourists": cur_m, "base": base_m}).reset_index()
    comp = comp[comp["market_name"] != "Abroad (unallocated)"]
    comp["change"] = comp["tourists"] / comp["base"] - 1

    a, b = st.columns(2)
    with a:
        st.markdown(f"**Tourists by source market, {m_year}**")
        st.plotly_chart(charts.hbar(comp, "market_name", "tourists", MODE, ",.0f", x_format="~s"), **PLOT)
    with b:
        st.markdown(f"**Change {m_base} → {m_year}**")
        st.plotly_chart(charts.hbar(comp, "market_name", "change", MODE, "+.0%", x_format="+.0%", diverging=True),
                        **PLOT)
    st.caption("FRONTUR (IBESTAT) counts every tourist, whatever the accommodation. "
               "Spain excludes Balearic residents. Cells IBESTAT suppressed for confidentiality are left out here.")

    st.markdown("**Tourists per year by market**")
    mm = by_market[by_market["year"].isin(m_years) & (by_market["market_name"] != "Abroad (unallocated)")]
    market_order = comp.sort_values("tourists", ascending=False)["market_name"].tolist()
    fig = charts.small_multiples(mm, "year", "tourists", "market_name", market_order, MODE, ",.0f",
                                 cols=4, height_per_row=180, y_format="~s")
    st.plotly_chart(fig, **PLOT)

    a, b = st.columns(2)
    with a:
        st.markdown("**Spending per tourist-day by market (€, EGATUR)**")
        s_years = complete_years(spending, "spending_eur")
        sp = filter_islands(spending, island)
        sp = sp[sp["year"].isin(s_years) & (sp["egatur_market_code"] != "ABROAD_UNALLOCATED")]
        sp = sp.groupby(["year", "egatur_market_name"], as_index=False)[["spending_eur", "tourist_days"]].sum()
        sp["per_day"] = sp["spending_eur"] / sp["tourist_days"]
        egatur_order = ["Germany", "United Kingdom", "Other abroad", "Spain (excl. Balearic Islands)"]
        egatur_colors = dict(zip(egatur_order, charts.THEMES[MODE]["series"]))
        fig = charts.lines(sp, "year", "per_day", "egatur_market_name", egatur_order, egatur_colors, MODE, "€,.0f",
                           height=340, markers=True, zero_base=False)
        st.plotly_chart(fig, **PLOT)
        st.caption("EGATUR only splits Germany, the UK, other countries and Spain. Includes all accommodation types.")
    with b:
        st.markdown("**Hotel nights by foreign residents (% of all hotel nights)**")
        fr = hotel_rates(hotel[hotel["year"].isin(hotel_years) & hotel["island_name"].isin(ISLANDS)],
                         ["year", "island_name"])
        fig = charts.lines(fr, "year", "share_abroad", "island_name",
                           ISLANDS if island == "All islands" else [island], COLORS, MODE, ".1%",
                           y_format=".0%", height=340, markers=True, zero_base=False)
        st.plotly_chart(fig, **PLOT)
        st.caption("INE hotel survey. INE only splits residents of Spain vs abroad at island level; "
                   "the country breakdown above comes from FRONTUR.")

# --------------------------------------------------------------------------- airports
with tab_air:
    st.subheader("How many arriving passengers end up in hotels?")
    air_years = sorted(set(complete_years(monthly, "airport_arrivals")) & set(hotel_years))
    am = monthly[monthly["island_name"].isin(ISLANDS) & monthly["year"].isin(air_years)]
    ay = am.groupby(["year", "island_name"], as_index=False)[["hotel_travellers", "airport_arrivals"]].sum(min_count=1)
    ay["ratio"] = ay["hotel_travellers"] / ay["airport_arrivals"]
    ay = ay[ay["year"] != 2020]  # 2020: island hotel figures largely suppressed (Unallocated)
    a, b = st.columns(2)
    with a:
        st.markdown("**Hotel guests per arriving air passenger**")
        fig = charts.lines(ay, "year", "ratio", "island_name", ISLANDS if island == "All islands" else [island],
                           COLORS, MODE, ".2f", y_format=".1f", height=360, markers=True)
        st.plotly_chart(fig, **PLOT)
        st.caption("A proxy, not a conversion rate: arrivals include residents and holiday-home tourists, and "
                   "hotel guests include people who came by sea or moved between islands. 2020 left out.")
    with b:
        st.markdown(f"**Monthly arriving passengers and hotel guests, {scope_label}**")
        sel = monthly if island == "All islands" else monthly[monthly["island_name"] == island]
        mo = sel.groupby("month_start", as_index=False)[["airport_arrivals", "hotel_travellers"]].sum(min_count=1)
        mo = mo[mo["month_start"] >= pd.Timestamp("2015-01-01")]
        mo = mo.melt(id_vars="month_start", var_name="measure", value_name="people")
        mo["measure"] = mo["measure"].map({"airport_arrivals": "Arriving passengers", "hotel_travellers": "Hotel guests"})
        mcol = {"Arriving passengers": charts.THEMES[MODE]["series"][0], "Hotel guests": charts.THEMES[MODE]["series"][1]}
        fig = charts.lines(mo, "month_start", "people", "measure", ["Arriving passengers", "Hotel guests"], mcol, MODE,
                           ",.0f", y_format="~s", height=360)
        st.plotly_chart(fig, **PLOT)
        st.caption("Both series count people, so they share one axis. Airports: Eurostat (avia_paoa).")

# --------------------------------------------------------------------------- data & method
with tab_data:
    st.subheader("Hotel KPIs by destination and month")
    kp = hotel_rates(hotel_sel, ["year_month", "destination_name", "island_name"])
    kp = kp.sort_values(["year_month", "destination_name"], ascending=[False, True])
    cols = ["year_month", "island_name", "destination_name", "travellers", "overnight_stays", "average_stay_nights",
            "room_occupancy_rate", "adr_eur", "revpar_eur", "is_provisional"]
    st.dataframe(
        kp[cols], hide_index=True, height=420,
        column_config={
            "year_month": "Month", "island_name": "Island", "destination_name": "Destination",
            "travellers": st.column_config.NumberColumn("Travellers", format="localized"),
            "overnight_stays": st.column_config.NumberColumn("Overnight stays", format="localized"),
            "average_stay_nights": st.column_config.NumberColumn("Avg stay", format="%.2f"),
            "room_occupancy_rate": st.column_config.NumberColumn("Room occupancy", format="percent"),
            "adr_eur": st.column_config.NumberColumn("ADR (€)", format="%.2f"),
            "revpar_eur": st.column_config.NumberColumn("RevPAR (€)", format="%.2f"),
            "is_provisional": "Provisional",
        },
    )
    st.download_button("Download as CSV", kp[cols].to_csv(index=False).encode(), "hotel_kpis.csv", "text/csv")
    st.markdown(
        """
**How the numbers are built**

- Source tables: INE hotel occupancy survey (EOH) and hotel profitability survey (IRSH), Eurostat airport
  traffic (`avia_paoa`), IBESTAT FRONTUR (tourist arrivals) and EGATUR (spending).
- The dbt warehouse stores additive components (room-nights, revenue, rooms sold). Every rate shown here is
  recomputed as *sum of numerator / sum of denominator* at the level displayed, never as an average of rates.
- Destinations: INE's *Isla de Mallorca* contains *Palma - Calvià*, so the model splits Mallorca into
  Palma - Calvià and a derived *Rest of Mallorca*.
- **Unallocated:** when INE suppresses an island (mostly Menorca and Ibiza in winter, and May–June 2020), the
  gap to the province total is kept as an *Unallocated* destination. It counts towards "All islands" demand
  but has no occupancy or price data.
- **ADR and RevPAR** start in January 2021, when INE's IRSH series begins.

Code and tests: see the repository README.
"""
    )
