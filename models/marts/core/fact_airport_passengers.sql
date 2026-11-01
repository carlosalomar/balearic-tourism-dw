-- Airport passengers (arrivals + departures, and arrivals only).
-- Grain: month x island (one airport per island) x flight scope (domestic / international).
select
    airport.date_key,
    island.island_key,
    airport.flight_scope,
    airport.passengers,
    airport.arriving_passengers
from {{ ref('stg_eurostat__airport_passengers') }} as airport
inner join {{ ref('island') }} as island on island.airport_code = airport.airport_code
