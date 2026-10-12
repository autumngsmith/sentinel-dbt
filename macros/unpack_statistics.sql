{% macro unpack_statistics(column) %}

{%- set stat_fields = [
    'nodata',
    'high_proba_clouds',
    'medium_proba_clouds',
    'thin_cirrus',
    'cloud_shadow',
    'dark_area',
    'vegetation',
    'not_vegetated',
    'water',
    'unclassified',
    'saturated_defective'
] -%}

{%- for field in stat_fields %}
        cast({{ column }} ->> '{{ field }}' as double) as {{ field }}_pct{{ "," if not loop.last }}
{%- endfor %}

{%- endmacro %}
