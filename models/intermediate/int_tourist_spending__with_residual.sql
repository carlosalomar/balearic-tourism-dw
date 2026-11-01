-- EGATUR spending and tourist days per island and EGATUR market, with the
-- suppressed cells collected in "Abroad (unallocated)" as in FRONTUR.
with egatur as (
    select * from {{ ref('stg_ibestat__egatur_spending') }}
),

markets as (
    select * from {{ ref('egatur_market') }} where ibestat_code is not null
),

published as (
    select egatur.date_key, egatur.ibestat_island_code, markets.egatur_market_code,
           egatur.spending_eur, egatur.tourist_days
    from egatur
    inner join markets on markets.ibestat_code = egatur.ibestat_market_code
    where egatur.spending_eur is not null
),

island_total as (
    select date_key, ibestat_island_code, spending_eur, tourist_days
    from egatur
    where ibestat_market_code = '5000_XIB'
),

published_sum as (
    select date_key, ibestat_island_code,
           sum(spending_eur) as spending_eur, sum(tourist_days) as tourist_days
    from published
    group by all
),

residual as (
    select
        island_total.date_key,
        island_total.ibestat_island_code,
        'ABROAD_UNALLOCATED' as egatur_market_code,
        island_total.spending_eur - coalesce(published_sum.spending_eur, 0) as spending_eur,
        island_total.tourist_days - coalesce(published_sum.tourist_days, 0) as tourist_days
    from island_total
    left join published_sum using (date_key, ibestat_island_code)
    -- spending is published in millions with two decimals: ignore rounding gaps
    where abs(island_total.spending_eur - coalesce(published_sum.spending_eur, 0)) > 50000
)

select * from published
union all
select * from residual
