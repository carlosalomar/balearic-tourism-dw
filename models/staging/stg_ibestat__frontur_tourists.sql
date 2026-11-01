-- FRONTUR tourists by island, country of residence and month.
-- Annual rows (TIME_PERIOD = '2015') and the Balearic total (ES53) are dropped.
with source as (
    select * from {{ source('raw', 'ibestat_frontur_tourists') }}
    where medidas = 'TURISTAS'
      and time_period like '%-M%'
)

select
    cast(replace(time_period, '-M', '') as integer) as date_key,
    territorio as ibestat_island_code,
    lugar_residencia as ibestat_market_code,
    value as tourists
from source
where territorio <> 'ES53'
