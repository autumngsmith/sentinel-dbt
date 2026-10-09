with source as (
    select * from {{ source('locations', 'chicago') }}
),

main as (
    select * from source
)

select * from main
