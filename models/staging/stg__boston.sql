with source as (
    select * from {{ source('locations', 'boston') }}
),

main as (
    select * from source
)

select * from main
