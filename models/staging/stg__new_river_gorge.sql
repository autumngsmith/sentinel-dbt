with source as (
    select * from {{ source('locations', 'new_river_gorge') }}
),

main as (
    select * from source
)

select * from main
