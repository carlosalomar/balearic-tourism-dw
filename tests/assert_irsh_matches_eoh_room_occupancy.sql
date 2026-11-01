-- Two surveys, one quantity: rooms sold (IRSH revenue / ADR) and occupied
-- room-nights (EOH occupancy rate x rooms) must agree within 5 percentage points
-- of occupancy in the high season. Off-season months, with few hotels open,
-- diverge more, and provisional months are still revised, so neither is checked.
select f.*
from {{ ref('fact_hotel_performance') }} as f
inner join {{ ref('dim_date') }} as d using (date_key)
where d.season = 'High'
  and not f.is_provisional
  and f.rooms_sold is not null
  and abs(f.rooms_sold - f.occupied_room_nights) / nullif(f.available_room_nights, 0) > 0.05
