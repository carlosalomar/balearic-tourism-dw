-- Monthly calendar shared by every fact (conformed dimension). Grain: one row per month.
with bounds as (
    select max(date_key) as last_key
    from (
        select date_key from {{ ref('stg_ine__eoh_province_demand') }}
        union all select date_key from {{ ref('stg_eurostat__airport_passengers') }}
        union all select date_key from {{ ref('stg_ibestat__frontur_tourists') }}
    )
),

months as (
    select cast(month_start as date) as month_start
    from bounds,
        generate_series(
            date '{{ var("first_month") }}',
            make_date(last_key // 100, last_key % 100, 1),
            interval 1 month
        ) as t(month_start)
)

select
    cast(strftime(month_start, '%Y%m') as integer) as date_key,
    month_start,
    last_day(month_start) as month_end,
    strftime(month_start, '%Y-%m') as year_month,
    year(month_start) as year,
    quarter(month_start) as quarter,
    month(month_start) as month,
    strftime(month_start, '%B') as month_name,
    strftime(month_start, '%b') as month_short_name,
    day(last_day(month_start)) as days_in_month,
    case
        when month(month_start) between 6 and 9 then 'High'
        when month(month_start) in (4, 5, 10) then 'Shoulder'
        else 'Low'
    end as season,
    -- Hotels were closed by decree or barely open; useful to exclude from trends.
    month_start between date '2020-03-01' and date '2021-05-01' as is_covid_period
from months
