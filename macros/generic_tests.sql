{#- Generic tests written here so the project needs no external packages. -#}

{% test non_negative(model, column_name, tolerance=0) %}
select *
from {{ model }}
where {{ column_name }} < -{{ tolerance }}
{% endtest %}

{% test unique_combination(model, combination_of_columns) %}
select {{ combination_of_columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ combination_of_columns | join(', ') }}
having count(*) > 1
{% endtest %}

{% test between(model, column_name, min_value, max_value) %}
select *
from {{ model }}
where {{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }}
{% endtest %}
