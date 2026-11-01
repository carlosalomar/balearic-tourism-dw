-- Hotel supply and occupancy rates by INE tourist zone, one row per zone and month.
with source as (
    select * from {{ source('raw', 'ine_eoh_zone_supply') }}
    where value is not null
)

select
    {{ month_key('year', 'month') }} as date_key,
    case zonas_turisticas
        when 'Baleares (Illes): Isla De Mallorca' then 'MALLORCA_ISLAND'
        when 'Baleares (Illes): Palma - Calvía' then 'PALMA_CALVIA'
        when 'Baleares (Illes): Isla De Menorca' then 'MENORCA'
        when 'Baleares (Illes): Islas De Ibiza-Formentera' then 'IBIZA_FORMENTERA'
    end as ine_zone_code,
    max(value) filter (where concepto_turistico = 'Número de establecimientos abiertos estimados') as establishments,
    max(value) filter (where concepto_turistico = 'Número de plazas estimadas') as bed_places,
    max(value) filter (where concepto_turistico = 'Número de habitaciones estimadas') as rooms,  -- published since 2015
    max(value) filter (where concepto_turistico = 'Personal empleado') as staff,
    max(value) filter (where concepto_turistico = 'Grado de ocupación por plazas') / 100 as bed_occupancy_rate,
    max(value) filter (where concepto_turistico = 'Grado de ocupación por plazas en fin de semana') / 100 as weekend_bed_occupancy_rate,
    max(value) filter (where concepto_turistico = 'Grado de ocupación por habitaciones') / 100 as room_occupancy_rate,
    bool_or(data_status = 'Provisional') as is_provisional
from source
group by all
