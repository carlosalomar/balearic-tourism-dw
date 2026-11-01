-- Domestic + international passengers must equal the TOTAL coverage Eurostat
-- publishes, which is why staging keeps only the two scopes.
with raw as (
    select rep_airp, tra_meas, time,
           sum(value) filter (where tra_cov = 'TOTAL') as total,
           sum(value) filter (where tra_cov in ('NAT', 'INTL')) as scopes
    from {{ source('raw', 'eurostat_avia_paoa') }}
    where schedule = 'TOTAL'
    group by all
)

select * from raw where total <> scopes
