-- FRONTUR markets per island. IBESTAT suppresses small cells, so the published
-- markets do not always add up to the island total; the gap goes to an
-- "Abroad (unallocated)" member (Spain is never suppressed). Gaps of a few
-- tourists are rounding differences between published figures and are ignored.
with frontur as (
    select * from {{ ref('stg_ibestat__frontur_tourists') }}
),

markets as (
    select * from {{ ref('origin') }} where ibestat_code is not null
),

published as (
    select frontur.date_key, frontur.ibestat_island_code, markets.origin_code, frontur.tourists
    from frontur
    inner join markets on markets.ibestat_code = frontur.ibestat_market_code
    where frontur.tourists is not null
),

island_total as (
    select date_key, ibestat_island_code, tourists
    from frontur
    where ibestat_market_code = '5000_XIB'  -- world excluding the Balearic Islands
),

published_sum as (
    select date_key, ibestat_island_code, sum(tourists) as tourists
    from published
    group by all
),

residual as (
    select
        island_total.date_key,
        island_total.ibestat_island_code,
        'ABROAD_UNALLOCATED' as origin_code,
        island_total.tourists - coalesce(published_sum.tourists, 0) as tourists
    from island_total
    left join published_sum using (date_key, ibestat_island_code)
    where abs(island_total.tourists - coalesce(published_sum.tourists, 0)) > 10
)

select * from published
union all
select * from residual
