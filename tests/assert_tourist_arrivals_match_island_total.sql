-- FRONTUR markets (published + Abroad unallocated) must add up to the island
-- total, up to the rounding gap left out of the residual.
with fact as (
    select f.date_key, i.ibestat_island_code, sum(f.tourists) as tourists
    from {{ ref('fact_tourist_arrivals') }} as f
    inner join {{ ref('dim_island') }} as i using (island_key)
    group by all
),

total as (
    select date_key, ibestat_island_code, tourists
    from {{ ref('stg_ibestat__frontur_tourists') }}
    where ibestat_market_code = '5000_XIB'
)

select *
from total
full outer join fact using (date_key, ibestat_island_code)
where abs(coalesce(total.tourists, 0) - coalesce(fact.tourists, 0)) > 10
