WITH title_genre AS (
    SELECT 
        tpr.title_id,    
        g.genre_id        
    FROM {{ ref('title') }} t
    JOIN {{ ref('genre_title') }} tg ON t.title_id = tg.title_id
    JOIN {{ ref('genre') }} g ON tg.genre_id = g.genre_id
), title_genre_aggregation AS (
        SELECT 
            title_id,
            ARRAY_AGG(genre_id) AS genre_ids,
            COUNT(genre_id) AS genre_count
        FROM title_genre
        GROUP BY title_id
)
SELECT
    tga.title_id,
    tga.genre_ids,
    tga.genre_count,
    t.release_year,
    t.average_rating,
    t.number_of_votes
FROM title_genre_aggregation tga
JOIN {{ ref('title') }} t ON tga.title_id = t.title_id        
