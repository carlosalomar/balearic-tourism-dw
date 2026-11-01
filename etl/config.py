"""Source configuration: which public tables feed the warehouse."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
INE_RAW = RAW_DIR / "ine"
AIRPORT_RAW = RAW_DIR / "airports"

INE_API = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{table_id}"

# INE tables (Tempus3 ids). Granularity checked against the API metadata.
INE_TABLES = {
    # Hotel Occupancy Survey (EOH)
    "eoh_zone_travellers_nights": 2039,   # tourist zone x residence (Spain / abroad)
    "eoh_zone_supply_occupancy": 2013,    # tourist zone: establishments, beds, occupancy %, staff
    "eoh_province_travellers_nights": 2074,  # region/province x residence
    "eoh_country_travellers_nights": 2038,   # country of residence, national level only
    # Hotel Sector Profitability Indicators (IRSH)
    "irsh_zone_adr": 46297,               # average daily rate by tourist zone
    "irsh_zone_revpar": 46300,            # revenue per available room by tourist zone
}

# Rows whose name contains this string belong to the Balearic Islands.
BALEARIC_TAG = "Baleares"

# Eurostat monthly passengers per airport (data reported by AENA).
EUROSTAT_API = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/avia_paoa"
)
AIRPORTS = {
    "ES_LEPA": {"iata": "PMI", "name": "Palma de Mallorca", "island": "Mallorca"},
    "ES_LEIB": {"iata": "IBZ", "name": "Ibiza", "island": "Ibiza-Formentera"},
    "ES_LEMH": {"iata": "MAH", "name": "Menorca", "island": "Menorca"},
}

# IBESTAT (Balearic statistics institute) eDatos / Metamac API.
# FRONTUR is the only public source with country of residence x island.
IBESTAT_RAW = RAW_DIR / "ibestat"
IBESTAT_API = "https://ibestat.es/edatos/apis/statistical-resources/v1.0/datasets/IBESTAT/{dataset_id}"
IBESTAT_DATASETS = {
    "frontur_tourists_island_residence": "000058A_000002",  # tourists: island x residence (8 markets) x month
    "egatur_spending_island_residence": "000059A_000007",   # spending: island x residence (DE, GB, ES, other) x month
    "egatur_nights_island_residence": "000059A_000011",     # tourist nights / avg stay: island x Spain/abroad x month
}
