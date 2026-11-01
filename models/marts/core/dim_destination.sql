-- Hotel destinations: additive leaves of the INE tourist zones, rolled up to island.
select
    destination.destination_key,
    destination.destination_code,
    destination.destination_name,
    destination.is_derived,
    destination.description,
    destination.island_key,
    island.island_name
from {{ ref('destination') }} as destination
inner join {{ ref('island') }} as island using (island_key)
