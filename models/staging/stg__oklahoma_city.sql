with source as (
    select * from {{ source('locations', 'oklahoma_city') }}
),

main as (
    select * from source
)

select * from main
