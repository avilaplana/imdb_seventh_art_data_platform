SELECT
    dt.title_id,
    g.genre_name,
    dt.title_type_name,
    dt.release_year,
    dt.is_adult,
    dt.average_rating,
    dt.number_of_votes
FROM {{ ref('dim_title') }} dt
JOIN {{ source('stage_canonical', 'genre_title') }} tg ON dt.title_id = tg.title_id
JOIN {{ source('stage_canonical', 'genre') }} g ON tg.genre_id = g.genre_id
