with source as (
    select * from {{ source('locations', 'miami') }}
),

main as (
    select * from source
)

select * from main
