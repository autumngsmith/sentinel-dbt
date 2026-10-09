with source as (
    select * from {{ source('locations', 'seattle') }}
),

main as (
    select * from source
)

select * from main
