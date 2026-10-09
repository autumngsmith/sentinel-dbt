{% macro get_locations() %} 

{% set count_types_query %}
select location_object_name, alias_name, filters, event_date
from {{ ref('locations') }}
{% endset %}

{% set types = run_query(count_types_query) %}

{% if execute %}
{# put each item into the dict #}

{% set types_dict = [] %}

{% for row in types.rows %}
    {% set row_dict = {
        "object_name" : row[0], 
        "alias" : row[1], 
        "filters" : row[2], 
        "event_date" : row[3]
    }
    %}

{% do types_dict.append(row_dict) %}
{% endfor %}
{% endif %}

{{ return(types_dict) }}

{% endmacro %}