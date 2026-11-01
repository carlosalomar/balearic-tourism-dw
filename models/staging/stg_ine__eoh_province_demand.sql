-- Travellers and overnight stays for the whole province (always published).
-- Table 2074 repeats the series at region and province level; Illes Balears is
-- a single-province region, so the province rows are kept.
with source as (
    select * from {{ source('raw', 'ine_eoh_province_demand') }}
    where provincias is not null
      and residencia_origen in ('Residentes en España', 'Residentes en el Extranjero')
      and value is not null
)

select
    {{ month_key('year', 'month') }} as date_key,
    case residencia_origen
        when 'Residentes en España' then 'SPAIN'
        else 'ABROAD'
    end as residence_code,
    sum(value) filter (where concepto_turistico = 'Viajero') as travellers,
    sum(value) filter (where concepto_turistico = 'Pernoctaciones') as overnight_stays,
    bool_or(data_status = 'Provisional') as is_provisional
from source
group by all
