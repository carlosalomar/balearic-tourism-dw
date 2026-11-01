-- Tourist spending (EGATUR), all accommodation types.
-- Grain: month x island x EGATUR market. EGATUR publishes only Germany, UK,
-- other abroad and Spain, so this fact uses the shrunken dim_egatur_market
-- instead of dim_origin. tourist_days = spending / spending per person-day.
select
    spending.date_key,
    island.island_key,
    market.egatur_market_key,
    spending.spending_eur,
    spending.tourist_days
from {{ ref('int_tourist_spending__with_residual') }} as spending
inner join {{ ref('island') }} as island on island.ibestat_code = spending.ibestat_island_code
inner join {{ ref('egatur_market') }} as market using (egatur_market_code)
