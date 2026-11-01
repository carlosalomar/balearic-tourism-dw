-- Travellers and overnight stays by INE tourist zone and residence, one row per month.
with source as (
    select * from {{ source('raw', 'ine_eoh_zone_demand') }}
    where value is not null  -- suppressed winter cells come as nulls
),

renamed as (
    select
        {{ month_key('year', 'month') }} as date_key,
        case zonas_turisticas
            when 'Baleares (Illes): Isla De Mallorca' then 'MALLORCA_ISLAND'
            when 'Baleares (Illes): Palma - Calvía' then 'PALMA_CALVIA'
            when 'Baleares (Illes): Isla De Menorca' then 'MENORCA'
            when 'Baleares (Illes): Islas De Ibiza-Formentera' then 'IBIZA_FORMENTERA'
        end as ine_zone_code,
        case residencia_origen
            when 'Residentes en España' then 'SPAIN'
            when 'Residentes en el Extranjero' then 'ABROAD'
        end as residence_code,
        case concepto_turistico
            when 'Viajero' then 'travellers'
            when 'Pernoctaciones' then 'overnight_stays'
        end as measure,
        value,
        data_status = 'Provisional' as is_provisional
    from source
)

select
    date_key,
    ine_zone_code,
    residence_code,
    sum(value) filter (where measure = 'travellers') as travellers,
    sum(value) filter (where measure = 'overnight_stays') as overnight_stays,
    bool_or(is_provisional) as is_provisional
from renamed
group by all
