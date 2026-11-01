-- Turns the overlapping INE tourist zones into additive destination leaves:
--   * Isla de Mallorca contains Palma - Calvià, so Rest of Mallorca = Mallorca - Palma - Calvià.
--   * Unallocated = province total - published islands, only in months where INE
--     suppresses at least one island (winter) or every zone (May-June 2020).
-- In fully published months the islands match the province within +-2 (rounding),
-- so no Unallocated row is created and the leaves add up to the province
-- within that tolerance (tests/assert_hotel_demand_matches_province.sql).
with zone as (
    select * from {{ ref('stg_ine__eoh_zone_demand') }}
),

province as (
    select * from {{ ref('stg_ine__eoh_province_demand') }}
),

published_leaves as (
    select date_key, ine_zone_code as destination_code, residence_code,
           travellers, overnight_stays, is_provisional
    from zone
    where ine_zone_code in ('PALMA_CALVIA', 'MENORCA', 'IBIZA_FORMENTERA')
),

rest_of_mallorca as (
    select
        mallorca.date_key,
        'REST_OF_MALLORCA' as destination_code,
        mallorca.residence_code,
        mallorca.travellers - palma.travellers as travellers,
        mallorca.overnight_stays - palma.overnight_stays as overnight_stays,
        mallorca.is_provisional or palma.is_provisional as is_provisional
    from zone as mallorca
    inner join zone as palma
        on  palma.date_key = mallorca.date_key
        and palma.residence_code = mallorca.residence_code
        and palma.ine_zone_code = 'PALMA_CALVIA'
    where mallorca.ine_zone_code = 'MALLORCA_ISLAND'
),

published_islands as (
    select date_key, residence_code,
           sum(travellers) as travellers,
           sum(overnight_stays) as overnight_stays,
           count(*) as n_islands
    from zone
    where ine_zone_code in ('MALLORCA_ISLAND', 'MENORCA', 'IBIZA_FORMENTERA')
    group by all
),

unallocated as (
    select
        province.date_key,
        'UNALLOCATED' as destination_code,
        province.residence_code,
        province.travellers - coalesce(islands.travellers, 0) as travellers,
        province.overnight_stays - coalesce(islands.overnight_stays, 0) as overnight_stays,
        province.is_provisional
    from province
    left join published_islands as islands using (date_key, residence_code)
    where coalesce(islands.n_islands, 0) < 3
)

select * from published_leaves
union all
select * from rest_of_mallorca
union all
select * from unallocated
