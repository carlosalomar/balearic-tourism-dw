-- EGATUR markets: a shrunken rollup of dim_origin (spending is published for fewer countries).
select
    market.egatur_market_key,
    market.egatur_market_code,
    market.egatur_market_name,
    market.residence_key,
    residence.residence_name
from {{ ref('egatur_market') }} as market
inner join {{ ref('residence') }} as residence using (residence_key)
