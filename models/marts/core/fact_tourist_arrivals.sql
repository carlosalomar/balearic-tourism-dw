-- Tourists arriving from outside the Balearic Islands (FRONTUR), all accommodation types.
-- Grain: month x island x source market. Fully additive; starts in October 2015.
select
    arrivals.date_key,
    island.island_key,
    origin.origin_key,
    cast(arrivals.tourists as bigint) as tourists
from {{ ref('int_tourist_arrivals__with_residual') }} as arrivals
inner join {{ ref('island') }} as island on island.ibestat_code = arrivals.ibestat_island_code
inner join {{ ref('origin') }} as origin using (origin_code)
