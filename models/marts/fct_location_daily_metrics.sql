-- depends_on: {{ ref('stg__boston') }}
-- depends_on: {{ ref('stg__chicago') }}
-- depends_on: {{ ref('stg__los_angeles') }}
-- depends_on: {{ ref('stg__mexico_city') }}
-- depends_on: {{ ref('stg__miami') }}
-- depends_on: {{ ref('stg__monterrey') }}
-- depends_on: {{ ref('stg__new_river_gorge') }}
-- depends_on: {{ ref('stg__oklahoma_city') }}
-- depends_on: {{ ref('stg__phoenix') }}
-- depends_on: {{ ref('stg__seattle') }}
-- depends_on: {{ ref('stg__tuxtla_gutierrez') }}
-- depends_on: {{ ref('stg__yellowstone') }}
-- depends_on: {{ ref('locations') }}
{{ config(
  persist_docs={"relation": true, "columns": false}
) }}
{%- set locations = get_locations() -%}

with {% for location in locations -%}
{{ location.alias }} as (
    select *
    from {{ ref(location.location_object_name) }}
    {{ location.filters or '' }}
),

-- {{ location.alias }}: one record per image from a source location

count_{{ location.alias }} as (
    select
        {{ location.alias }}_scene_id as scene_id, 
        {{ location.event_date }} as event_date,
        '{{ location.alias }}' as location_name,
        cloud_cover_pct,
        nodata_pct,
        1 as num_images
    from {{ location.alias }}

),

{% endfor -%} 

unioned_locations as (

    {%- for location in locations %}
    select * from count_{{ location.alias }}
    {%- if loop.last %}
    {% else %}
    union all 
    {%- endif -%}
    {%- endfor %}
),


main as (
    select
        *,
        {{ dbt_utils.generate_surrogate_key([ 
            'scene_id',
            'event_date'
        ]) }} as unique_image_id
    from unioned_locations
)

select * from main 
