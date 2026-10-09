with source as (
    select * from {{ source('locations', 'tuxtla_gutierrez') }}
),

main as (
    select * from source
)

select * from main
