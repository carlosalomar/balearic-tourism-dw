-- Hotel supply, occupancy and prices as additive components per destination leaf.
-- Rates are not additive, so they are converted into the quantities behind them:
--   available_bed_nights  = bed places x days in month
--   occupied_bed_nights   = bed occupancy rate x available bed-nights
--   available_room_nights = rooms x days in month              (rooms since 2015)
--   occupied_room_nights  = room occupancy rate x available room-nights
--   room_revenue_eur      = RevPAR x available room-nights      (IRSH, since 2021)
--   rooms_sold            = room revenue / ADR                  (IRSH, since 2021)
-- Rest of Mallorca is then Mallorca minus Palma - Calvià for every component.
-- The province supply is not downloaded, so there is no Unallocated leaf here:
-- islands suppressed in winter simply have no row.
with supply as (
    select * from {{ ref('stg_ine__eoh_zone_supply') }}
),

prices as (
    select * from {{ ref('stg_ine__irsh_zone_prices') }}
),

zone_components as (
    select
        supply.date_key,
        supply.ine_zone_code,
        supply.establishments,
        supply.bed_places,
        supply.rooms,
        supply.staff,
        supply.bed_places * days.days_in_month as available_bed_nights,
        supply.bed_occupancy_rate * supply.bed_places * days.days_in_month as occupied_bed_nights,
        supply.rooms * days.days_in_month as available_room_nights,
        supply.room_occupancy_rate * supply.rooms * days.days_in_month as occupied_room_nights,
        prices.revpar * supply.rooms * days.days_in_month as room_revenue_eur,
        prices.revpar * supply.rooms * days.days_in_month / nullif(prices.adr, 0) as rooms_sold,
        supply.is_provisional or coalesce(prices.is_provisional, false) as is_provisional
    from supply
    left join prices using (date_key, ine_zone_code)
    cross join lateral (
        select day(last_day(make_date(supply.date_key // 100, supply.date_key % 100, 1))) as days_in_month
    ) as days
),

{% set components = ['establishments', 'bed_places', 'rooms', 'staff',
                     'available_bed_nights', 'occupied_bed_nights',
                     'available_room_nights', 'occupied_room_nights',
                     'room_revenue_eur', 'rooms_sold'] %}

published_leaves as (
    select date_key, ine_zone_code as destination_code,
        {% for c in components %}{{ c }},{% endfor %}
        is_provisional
    from zone_components
    where ine_zone_code in ('PALMA_CALVIA', 'MENORCA', 'IBIZA_FORMENTERA')
),

rest_of_mallorca as (
    select
        mallorca.date_key,
        'REST_OF_MALLORCA' as destination_code,
        {% for c in components %}mallorca.{{ c }} - palma.{{ c }} as {{ c }},
        {% endfor %}mallorca.is_provisional or palma.is_provisional as is_provisional
    from zone_components as mallorca
    inner join zone_components as palma
        on palma.date_key = mallorca.date_key and palma.ine_zone_code = 'PALMA_CALVIA'
    where mallorca.ine_zone_code = 'MALLORCA_ISLAND'
)

select * from published_leaves
union all
select * from rest_of_mallorca
