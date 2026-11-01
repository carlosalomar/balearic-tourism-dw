-- Hotel travellers and overnight stays.
-- Grain: month x destination leaf x residence (Spain / abroad). Fully additive.
select
    demand.date_key,
    destination.destination_key,
    residence.residence_key,
    cast(demand.travellers as bigint) as travellers,
    cast(demand.overnight_stays as bigint) as overnight_stays,
    demand.is_provisional
from {{ ref('int_hotel_demand__destination_leaves') }} as demand
inner join {{ ref('destination') }} as destination using (destination_code)
inner join {{ ref('residence') }} as residence using (residence_code)
