with source as (
    select * from {{ source('locations', 'phoenix') }}
),

main as (
    select * from source
)

select * from main
