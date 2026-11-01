-- Islands: the shrunken rollup of dim_destination, used directly by the airport,
-- FRONTUR and EGATUR facts so all of them can be compared by island.
select
    island_key,
    island_code,
    island_name,
    airport_iata,
    airport_name,
    airport_code as eurostat_airport_code,
    ibestat_code as ibestat_island_code
from {{ ref('island') }}
