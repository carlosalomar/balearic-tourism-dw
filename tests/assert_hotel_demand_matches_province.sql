-- The destination leaves must add up to the province total published by INE
-- (table 2074) in every month and residence. Zone and province tables are
-- rounded independently, so a gap of a few units is accepted.
with leaves as (
    select date_key, residence_key,
           sum(travellers) as travellers, sum(overnight_stays) as overnight_stays
    from {{ ref('fact_hotel_demand') }}
    group by all
),

province as (
    select p.date_key, r.residence_key, p.travellers, p.overnight_stays
    from {{ ref('stg_ine__eoh_province_demand') }} as p
    inner join {{ ref('dim_residence') }} as r using (residence_code)
)

select *
from province
full outer join leaves using (date_key, residence_key)
where abs(coalesce(province.travellers, 0) - coalesce(leaves.travellers, 0)) > 3
   or abs(coalesce(province.overnight_stays, 0) - coalesce(leaves.overnight_stays, 0)) > 3
