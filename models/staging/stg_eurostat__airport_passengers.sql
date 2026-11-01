-- Monthly passengers per Balearic airport, split into domestic and international flights.
-- The TOTAL coverage is dropped here: it equals domestic + international exactly
-- (checked in tests/assert_airport_scopes_add_up.sql).
with source as (
    select * from {{ source('raw', 'eurostat_avia_paoa') }}
    where schedule = 'TOTAL' and tra_cov in ('NAT', 'INTL')
)

select
    cast(replace(time, '-', '') as integer) as date_key,
    rep_airp as airport_code,
    case tra_cov when 'NAT' then 'DOMESTIC' else 'INTERNATIONAL' end as flight_scope,
    sum(value) filter (where tra_meas = 'PAS_CRD') as passengers,
    sum(value) filter (where tra_meas = 'PAS_CRD_ARR') as arriving_passengers
from source
group by all
