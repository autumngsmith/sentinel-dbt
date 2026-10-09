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
{{ config(
  persist_docs={"relation": true, "columns": false}
) }}
{%- set locations = get_locations() -%}

with {% for location in locations -%}
{{ location.alias }} as (
    select *
    from {{ ref(location.location_object_name) }}
    {{ location.filters }}
    {%- endif %}
),

-- {{ location.alias }}: count the number of each location broken down by the grain

count_{{ location.alias }} as (
    select
        {{ regex_replace(location.location_object_name.split('__')[-1], 's$', '') }}_sfdc_id as sfdc_id, 
        {{ regex_replace(location.location_object_name.split('__')[-1], 's$', '') }}_id as id, 
        {{ location.event_date }} as event_date,
        '{{ location.alias }}' as change_type,
        null as bill_amount, 
        null as pay_amount,
        1 as num_events
    from {{ location.alias }}

),

{% endfor -%} 

unioned_funnel_checkpoints as (

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
            'sfdc_id',
            'id',
            'event_date'
        ]) }} as unique_location_id
    from unioned_funnel_checkpoints
)

select * from main 
