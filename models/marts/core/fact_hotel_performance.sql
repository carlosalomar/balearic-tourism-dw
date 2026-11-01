-- Hotel supply, occupancy and revenue components.
-- Grain: month x destination leaf. Flow measures (*_nights, revenue, rooms sold)
-- are fully additive; stock measures (establishments, bed places, rooms, staff)
-- add across destinations but not across months (average them over time).
-- Occupancy, ADR and RevPAR are recomputed from these in mart_hotel_kpis.
select
    perf.date_key,
    destination.destination_key,
    perf.establishments,
    perf.bed_places,
    perf.rooms,
    perf.staff,
    perf.available_bed_nights,
    perf.occupied_bed_nights,
    perf.available_room_nights,
    perf.occupied_room_nights,
    perf.room_revenue_eur,
    perf.rooms_sold,
    perf.is_provisional
from {{ ref('int_hotel_performance__destination_leaves') }} as perf
inner join {{ ref('destination') }} as destination using (destination_code)
