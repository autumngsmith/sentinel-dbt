with source as (
    select * from {{ source('locations', 'yellowstone') }}
),

main as (
    select * from source
)

select * from main
