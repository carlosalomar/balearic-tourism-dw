-- Hotel KPIs per destination and month, recomputed from additive components so
-- they also exist for the derived Rest of Mallorca.
-- Rates must be re-aggregated the same way: sum the components, then divide.
select
    perf.date_key,
    dates.year_month,
    dates.year,
    dates.month,
    dates.season,
    destination.destination_name,
    destination.island_name,
    perf.establishments,
    perf.bed_places,
    perf.rooms,
    perf.staff,
    demand.travellers,
    demand.overnight_stays,
    demand.overnight_stays / nullif(demand.travellers, 0) as average_stay_nights,
    perf.occupied_bed_nights / nullif(perf.available_bed_nights, 0) as bed_occupancy_rate,
    perf.occupied_room_nights / nullif(perf.available_room_nights, 0) as room_occupancy_rate,
    perf.room_revenue_eur / nullif(perf.rooms_sold, 0) as adr_eur,
    perf.room_revenue_eur / nullif(perf.available_room_nights, 0) as revpar_eur,
    perf.room_revenue_eur,
    perf.is_provisional
from {{ ref('fact_hotel_performance') }} as perf
inner join {{ ref('dim_date') }} as dates using (date_key)
inner join {{ ref('dim_destination') }} as destination using (destination_key)
left join (
    select date_key, destination_key,
           sum(travellers) as travellers, sum(overnight_stays) as overnight_stays
    from {{ ref('fact_hotel_demand') }}
    group by all
) as demand using (date_key, destination_key)
