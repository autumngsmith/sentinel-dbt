{#
    Reads the `locations` seed and returns one dict per location, which the
    monster model loops over. Returns an empty list at parse time, when dbt
    can't run queries yet.
#}
{% macro get_locations() %}

{% set locations = [] %}

{% if execute %}

    {% set locations_query %}
    select location_object_name, alias_name, filters, event_date
    from {{ ref('locations') }}
    {% endset %}

    {% set results = run_query(locations_query) %}

    {% for row in results.rows %}
        {% do locations.append({
            "location_object_name": row[0],
            "alias": row[1],
            "filters": row[2],
            "event_date": row[3]
        }) %}
    {% endfor %}

{% endif %}

{{ return(locations) }}

{% endmacro %}
