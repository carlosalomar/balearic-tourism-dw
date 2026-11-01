-- Drill-across by island and month: each fact is aggregated to the shared
-- grain (dim_date x dim_island) first, then the results are joined.
-- Hotel figures roll up from destinations; Unallocated hotel demand stays
-- under its own island member.
with hotel_demand as (
    select d.date_key, dest.island_key,
           sum(d.travellers) as hotel_travellers,
           sum(d.overnight_stays) as hotel_overnight_stays,
           sum(d.overnight_stays) filter (where res.residence_code = 'ABROAD') as hotel_overnight_stays_abroad
    from {{ ref('fact_hotel_demand') }} as d
    inner join {{ ref('dim_destination') }} as dest using (destination_key)
    inner join {{ ref('dim_residence') }} as res using (residence_key)
    group by all
),

hotel_performance as (
    select p.date_key, dest.island_key,
           sum(p.bed_places) as hotel_bed_places,
           sum(p.occupied_bed_nights) / nullif(sum(p.available_bed_nights), 0) as hotel_bed_occupancy_rate,
           sum(p.occupied_room_nights) / nullif(sum(p.available_room_nights), 0) as hotel_room_occupancy_rate,
           sum(p.room_revenue_eur) / nullif(sum(p.rooms_sold), 0) as hotel_adr_eur,
           sum(p.room_revenue_eur) / nullif(sum(p.available_room_nights), 0) as hotel_revpar_eur
    from {{ ref('fact_hotel_performance') }} as p
    inner join {{ ref('dim_destination') }} as dest using (destination_key)
    group by all
),

airport as (
    select date_key, island_key,
           sum(passengers) as airport_passengers,
           sum(arriving_passengers) as airport_arrivals,
           sum(arriving_passengers) filter (where flight_scope = 'INTERNATIONAL') as airport_international_arrivals
    from {{ ref('fact_airport_passengers') }}
    group by all
),

arrivals as (
    select a.date_key, a.island_key,
           sum(a.tourists) as tourists,
           sum(a.tourists) filter (where o.residence_code = 'ABROAD') as tourists_abroad
    from {{ ref('fact_tourist_arrivals') }} as a
    inner join {{ ref('dim_origin') }} as o_dim using (origin_key)
    inner join {{ ref('dim_residence') }} as o on o.residence_key = o_dim.residence_key
    group by all
),

spending as (
    select date_key, island_key,
           sum(spending_eur) as tourist_spending_eur,
           sum(tourist_days) as tourist_days
    from {{ ref('fact_tourist_spending') }}
    group by all
)

select
    dates.date_key,
    dates.year_month,
    dates.year,
    dates.month,
    dates.season,
    dates.is_covid_period,
    island.island_name,
    hotel_demand.hotel_travellers,
    hotel_demand.hotel_overnight_stays,
    hotel_demand.hotel_overnight_stays_abroad,
    hotel_performance.hotel_bed_places,
    hotel_performance.hotel_bed_occupancy_rate,
    hotel_performance.hotel_room_occupancy_rate,
    hotel_performance.hotel_adr_eur,
    hotel_performance.hotel_revpar_eur,
    airport.airport_passengers,
    airport.airport_arrivals,
    airport.airport_international_arrivals,
    arrivals.tourists,
    arrivals.tourists_abroad,
    spending.tourist_spending_eur,
    spending.tourist_days,
    spending.tourist_spending_eur / nullif(spending.tourist_days, 0) as spending_per_day_eur,
    -- share of FRONTUR tourists that stay in hotels is not observable; this ratio
    -- (hotel travellers per arriving passenger) is the closest proxy
    hotel_demand.hotel_travellers / nullif(airport.airport_arrivals, 0) as hotel_travellers_per_arrival
from {{ ref('dim_date') }} as dates
cross join {{ ref('dim_island') }} as island
left join hotel_demand using (date_key, island_key)
left join hotel_performance using (date_key, island_key)
left join airport using (date_key, island_key)
left join arrivals using (date_key, island_key)
left join spending using (date_key, island_key)
where coalesce(hotel_demand.hotel_travellers, airport.airport_passengers, arrivals.tourists) is not null
