with source as (
    select * from {{ source('locations', 'los_angeles') }}
),

main as (
    select * from source
)

select * from main
