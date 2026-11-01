-- tourist_days is derived as spending / spending per person-day. Summed over
-- markets it must reproduce the tourist nights EGATUR publishes separately
-- (dataset 000059A_000011) within 1 %.
with derived as (
    select f.date_key, i.ibestat_island_code, sum(f.tourist_days) as tourist_days
    from {{ ref('fact_tourist_spending') }} as f
    inner join {{ ref('dim_island') }} as i using (island_key)
    group by all
),

published as (
    select date_key, ibestat_island_code, tourist_nights
    from {{ ref('stg_ibestat__egatur_nights') }}
    where ibestat_market_code = '5000_XIB'
)

select *
from published
inner join derived using (date_key, ibestat_island_code)
where abs(derived.tourist_days - published.tourist_nights) > 0.01 * published.tourist_nights
