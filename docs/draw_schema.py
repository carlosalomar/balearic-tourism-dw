import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FACT, DIM, OPT = "#1f4e79", "#2e7d6b", "#9a9a9a"
fig, ax = plt.subplots(figsize=(18.5, 9))
ax.set_xlim(0, 18.5); ax.set_ylim(-0.2, 9); ax.axis("off")

def table(x, ytop, w, title, cols, color, dashed=False):
    h = 0.45 + 0.3 * len(cols)
    ls = "--" if dashed else "-"
    ax.add_patch(FancyBboxPatch((x, ytop - h), w, h, boxstyle="round,pad=0,rounding_size=0.08",
                 fc="white", ec=color, lw=2, ls=ls, zorder=3))
    ax.add_patch(FancyBboxPatch((x, ytop - 0.45), w, 0.45, boxstyle="round,pad=0,rounding_size=0.08",
                 fc=color, ec=color, lw=2, zorder=4))
    ax.text(x + w / 2, ytop - 0.225, title, ha="center", va="center", color="white",
            fontsize=11, weight="bold", zorder=5)
    for i, c in enumerate(cols):
        ax.text(x + 0.12, ytop - 0.45 - 0.3 * (i + 0.55), c, ha="left", va="center",
                fontsize=9, family="monospace", color="#222", zorder=5)
    return dict(l=(x, ytop - h / 2), r=(x + w, ytop - h / 2), t=(x + w / 2, ytop), b=(x + w / 2, ytop - h))

def link(a, b, color, dashed=False, label=None):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=1.5, ls="--" if dashed else "-", zorder=1)
    if label:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.12, label, ha="center", fontsize=8.5,
                color=color, style="italic")

date = table(7.6, 8.6, 3.6, "dim_date", ["date_key  PK (yyyymm)", "year, quarter, month", "days_in_month", "season, is_covid_period"], DIM)

dem = table(0.1, 6.0, 3.4, "fact_hotel_demand", ["date_key         FK", "destination_key  FK", "residence_key    FK", "travellers", "overnight_stays"], FACT)
perf = table(3.7, 6.0, 3.6, "fact_hotel_performance", ["date_key         FK", "destination_key  FK", "establishments, staff", "bed_places, rooms", "avail_bed/room_nights", "occupied_bed/room_nights", "room_revenue, rooms_sold"], FACT)
air = table(7.5, 6.0, 3.4, "fact_airport_passengers", ["date_key     FK", "island_key   FK", "flight_scope (dom/intl)", "passengers", "arriving_passengers"], FACT)
tour = table(11.1, 6.0, 3.4, "fact_tourist_arrivals", ["date_key     FK", "island_key   FK", "origin_key   FK", "tourists (FRONTUR)"], FACT)
spend = table(14.7, 6.0, 3.6, "fact_tourist_spending", ["date_key           FK", "island_key         FK", "egatur_market_key  FK", "spending_eur (EGATUR)", "tourist_days"], FACT)

res = table(0.1, 2.75, 3.4, "dim_residence", ["residence_key  PK", "Spain / Abroad"], DIM)
dest = table(3.9, 2.75, 3.4, "dim_destination", ["destination_key  PK", "destination_name", "is_derived", "island_key  FK"], DIM)
isl = table(7.7, 2.75, 3.0, "dim_island", ["island_key  PK", "island_name", "airport_iata"], DIM)
orig = table(11.1, 2.75, 3.4, "dim_origin", ["origin_key  PK", "market (DE, GB, FR...)", "egatur_market_key  FK", "residence_key  FK"], DIM)
emk = table(14.9, 2.75, 3.4, "dim_egatur_market", ["egatur_market_key  PK", "DE / GB / other / ES", "residence_key  FK"], DIM)

for f in (dem, perf, air, tour, spend):
    link(date["b"], f["t"], DIM)
link(dest["t"], dem["b"], DIM); link(dest["t"], perf["b"], DIM)
link(res["t"], dem["b"], DIM)
link(isl["t"], air["b"], DIM)
link(isl["t"], tour["b"], DIM)
link(isl["t"], spend["b"], DIM)
link(orig["t"], tour["b"], DIM)
link(emk["t"], spend["b"], DIM)
link(dest["r"], isl["l"], DIM)
link(orig["r"], emk["l"], DIM)
ax.plot([orig["b"][0], orig["b"][0], res["b"][0], res["b"][0]], [orig["b"][1], 0.95, 0.95, res["b"][1]],
        color=DIM, lw=1.5, ls="--", zorder=1)
ax.text(7.6, 0.78, "dim_origin rolls up to dim_egatur_market and dim_residence", ha="center", fontsize=8.5, color=DIM, style="italic")
legend = [("Fact", FACT, False), ("Dimension", DIM, False)]
for i, (lbl, c, d) in enumerate(legend):
    x = 0.3 + i * 1.6
    ax.add_patch(FancyBboxPatch((x, 7.75), 0.3, 0.22, boxstyle="round,pad=0", fc=c, ec=c))
    ax.text(x + 0.4, 7.86, lbl, va="center", fontsize=9.5)

ax.text(0.3, 8.75, "Balearic Tourism Data Warehouse", fontsize=16, weight="bold")
ax.text(0.3, 8.3, "Star schema with conformed dimensions (monthly grain)", fontsize=11, color="#555")
ax.text(0.1, 0.2,
        "Conformed dimensions: dim_date everywhere; dim_island is a shrunken rollup of dim_destination (hotel zones -> islands), and dim_egatur_market and dim_residence\n"
        "are rollups of dim_origin, which lets hotel, airport, FRONTUR and EGATUR facts be compared (drill-across). Destination leaves: Palma-Calvia, Rest of Mallorca (derived),\n"
        "Menorca, Ibiza-Formentera and Unallocated (derived: suppressed winter cells). Rates (occupancy, ADR, RevPAR) are computed from additive components in the marts.\n"
        "EGATUR spending is published only for Germany, UK, other abroad and Spain, so it has its own fact at that coarser grain.",
        fontsize=8.8, color="#444", va="center")
plt.savefig(__import__("pathlib").Path(__file__).with_name("schema.png"), dpi=150, bbox_inches="tight", facecolor="white")
