-- ADR and RevPAR (euros) by INE tourist zone. The IRSH survey starts in 2021.
with adr as (
    select zonas_turisticas, year, month, value as adr, data_status
    from {{ source('raw', 'ine_irsh_zone_adr') }}
    where tipo_de_dato = 'Dato' and value is not null
),

revpar as (
    select zonas_turisticas, year, month, value as revpar
    from {{ source('raw', 'ine_irsh_zone_revpar') }}
    where tipo_de_dato = 'Dato' and value is not null
)

select
    {{ month_key('adr.year', 'adr.month') }} as date_key,
    case adr.zonas_turisticas
        when 'Baleares (Illes): Isla De Mallorca' then 'MALLORCA_ISLAND'
        when 'Baleares (Illes): Palma - Calvía' then 'PALMA_CALVIA'
        when 'Baleares (Illes): Isla De Menorca' then 'MENORCA'
        when 'Baleares (Illes): Islas De Ibiza-Formentera' then 'IBIZA_FORMENTERA'
    end as ine_zone_code,
    adr.adr,
    revpar.revpar,
    adr.data_status = 'Provisional' as is_provisional
from adr
inner join revpar using (zonas_turisticas, year, month)
