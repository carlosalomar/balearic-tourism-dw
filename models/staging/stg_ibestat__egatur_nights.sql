-- EGATUR tourist nights (all accommodation types) by island and Spain / abroad.
-- Used to validate the tourist days derived from spending.
select
    cast(replace(time_period, '-M', '') as integer) as date_key,
    territorio as ibestat_island_code,
    lugar_residencia as ibestat_market_code,
    max(value) filter (where medidas = 'PERNOCTACION_TURISTICA') as tourist_nights,
    max(value) filter (where medidas = 'ESTANCIA_MEDIA') as average_stay
from {{ source('raw', 'ibestat_egatur_nights') }}
where time_period like '%-M%'
  and territorio <> 'ES53'
group by all
