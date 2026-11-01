-- FRONTUR source markets (country of residence), with their EGATUR market and
-- Spain / abroad rollups denormalised for convenience.
select
    origin.origin_key,
    origin.origin_code,
    origin.market_name,
    origin.egatur_market_key,
    market.egatur_market_name,
    origin.residence_key,
    residence.residence_name
from {{ ref('origin') }} as origin
inner join {{ ref('egatur_market') }} as market using (egatur_market_key)
inner join {{ ref('residence') }} as residence on residence.residence_key = origin.residence_key
