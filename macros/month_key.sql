{#- yyyymm integer key used by dim_date and every fact. -#}
{% macro month_key(year_col, month_col) -%}
    cast({{ year_col }} * 100 + {{ month_col }} as integer)
{%- endmacro %}
