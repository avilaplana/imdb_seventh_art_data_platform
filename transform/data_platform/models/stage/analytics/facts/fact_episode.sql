SELECT
    te.series_title_id,
    te.episode_title_id,
    te.season_number,
    te.episode_number,
    ep.primary_title    AS episode_primary_title,
    ep.release_year     AS episode_release_year,
    ep.average_rating   AS episode_average_rating,
    ep.number_of_votes  AS episode_number_of_votes,
    s.primary_title     AS series_primary_title,
    s.average_rating    AS series_average_rating
FROM {{ source('stage_canonical', 'title_episode') }} te
JOIN {{ source('stage_canonical', 'title') }} ep ON te.episode_title_id = ep.title_id
JOIN {{ source('stage_canonical', 'title') }} s  ON te.series_title_id  = s.title_id
