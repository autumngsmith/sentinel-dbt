with source as (
    select * from {{ source('locations', 'monterrey') }}
),

main as (
    select * from source
)

select * from main
