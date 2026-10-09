with source as (
    select * from {{ source('locations', 'mexico_city') }}
),

main as (
    select * from source
)

select * from main
