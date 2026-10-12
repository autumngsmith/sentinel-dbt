with source as (
    select * from {{ source('locations', 'seattle') }}
),

main as (
    select
        seattle_scene_id,
        tile_id as location_id,
        platform as satellite_name,
        acquired_at,
        cast(acquired_at at time zone 'UTC' as date) as event_date,
        published_at,
        updated_at,
        processing_version,
        cloud_cover as cloud_cover_pct,
        {{ unpack_statistics('statistics') }}
    from source
), 

deduplicated as (
    select *
    from main
    qualify row_number() over (
        partition by satellite_name, acquired_at, location_id
        order by processing_version desc, nodata_pct asc
    ) = 1
)

select * from deduplicated
