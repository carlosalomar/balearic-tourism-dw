-- EGATUR spending by island, market and month. Spending is published in
-- millions of euros; tourist_days is derived as spending / spending per person-day.
with source as (
    select * from {{ source('raw', 'ibestat_egatur_spending') }}
    where time_period like '%-M%'
      and territorio <> 'ES53'
),

pivoted as (
    select
        cast(replace(time_period, '-M', '') as integer) as date_key,
        territorio as ibestat_island_code,
        lugar_residencia as ibestat_market_code,
        max(value) filter (where medidas = 'GASTO_TURISTICO') * 1e6 as spending_eur,
        max(value) filter (where medidas = 'GASTO_TURISTICO_PERSONA') as spending_per_tourist_eur,
        max(value) filter (where medidas = 'GASTO_TURISTICO_PERSONA_DIA') as spending_per_day_eur
    from source
    group by all
)

select
    *,
    case when spending_eur = 0 then 0 else spending_eur / nullif(spending_per_day_eur, 0) end as tourist_days,
    case when spending_eur = 0 then 0 else spending_eur / nullif(spending_per_tourist_eur, 0) end as tourists
from pivoted
