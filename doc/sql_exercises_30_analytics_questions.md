# 45 SQL Questions — Analytics Layer (staged_analytics)

All queries target the `staged_analytics` schema (gold layer — Star Schema).

**Tables used:**
- `staged_analytics.dim_title` — core title dimension
- `staged_analytics.dim_person` — people dimension
- `staged_analytics.fact_title_genre_flat` — one row per title-genre (flat)
- `staged_analytics.fact_title_cast_crew` — title × person × role
- `staged_analytics.fact_title_release` — localized title releases by region/language
- `staged_analytics.fact_episode` — one row per episode with series context (season/episode numbers, ratings)

---

## Q01 — List the 10 highest-rated movies released in 2020

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating,
    number_of_votes
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND release_year = 2020
  AND number_of_votes > 0
ORDER BY average_rating DESC
LIMIT 10;
```

---

## Q02 — Show all movies released in 1999 with a rating of at least 8

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating,
    number_of_votes
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND release_year = 1999
  AND average_rating >= 8;
```

---

## Q03 — Find the details of the movie titled 'Inception'

```sql
SELECT *
FROM staged_analytics.dim_title
WHERE primary_title = 'Inception'
  AND title_type_name = 'movie';
```

---

## Q04 — List all movies released after 2015 marked as adult content

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    is_adult
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND release_year > 2015
  AND is_adult = TRUE;
```

---

## Q05 — Show all movies with a runtime longer than 150 minutes

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    duration_minutes
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND duration_minutes > 150
ORDER BY duration_minutes DESC;
```

---

## Q06 — Find all titles released in Spain in the Spanish language

```sql
SELECT
    ftr.title_id,
    dt.primary_title,
    dt.release_year,
    ftr.localized_title,
    ftr.region_name,
    ftr.language_name
FROM staged_analytics.fact_title_release ftr
JOIN staged_analytics.dim_title dt ON ftr.title_id = dt.title_id
WHERE ftr.region_name = 'Spain'
  AND ftr.language_name = 'Spanish';
```

---

## Q07 — List all movies that have no user rating yet

```sql
SELECT
    title_id,
    primary_title,
    release_year
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND (number_of_votes = 0 OR number_of_votes IS NULL);
```

---

## Q08 — Show all titles released in 2023 with their primary title and release year

```sql
SELECT
    title_id,
    primary_title,
    title_type_name,
    release_year
FROM staged_analytics.dim_title
WHERE release_year = 2023
ORDER BY primary_title;
```

---

## Q09 — List the first 20 titles in the catalog ordered by release year ascending

```sql
SELECT
    title_id,
    primary_title,
    title_type_name,
    release_year
FROM staged_analytics.dim_title
ORDER BY release_year ASC
LIMIT 20;
```

---

## Q10 — Show all movies whose primary title contains the word 'Star'

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND primary_title LIKE '%Star%'
ORDER BY release_year;
```

---

## Q11 — For each genre, the average rating of movies released after 2010

```sql
SELECT
    genre_name,
    ROUND(AVG(average_rating), 2) AS avg_rating,
    COUNT(DISTINCT title_id)       AS movie_count
FROM staged_analytics.fact_title_genre_flat
WHERE title_type_name = 'movie'
  AND release_year > 2010
  AND average_rating > 0
GROUP BY genre_name
ORDER BY avg_rating DESC;
```

---

## Q12 — Top 10 highest-rated Action movies of all time

```sql
SELECT
    ftg.title_id,
    dt.primary_title,
    dt.release_year,
    dt.average_rating,
    dt.number_of_votes
FROM staged_analytics.fact_title_genre_flat ftg
JOIN staged_analytics.dim_title dt ON ftg.title_id = dt.title_id
WHERE ftg.genre_name = 'Action'
  AND ftg.title_type_name = 'movie'
  AND dt.number_of_votes > 0
ORDER BY dt.average_rating DESC
LIMIT 10;
```

---

## Q13 — For each year since 2000, how many movies were released

```sql
SELECT
    release_year,
    COUNT(*) AS movie_count
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND release_year >= 2000
GROUP BY release_year
ORDER BY release_year;
```

---

## Q14 — The 20 most recent movies with their average rating and number of votes

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating,
    number_of_votes
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
ORDER BY release_year DESC
LIMIT 20;
```

---

## Q15 — All movies that belong to both 'Action' and 'Adventure' genres

```sql
SELECT
    dt.title_id,
    dt.primary_title,
    dt.release_year,
    dt.average_rating
FROM staged_analytics.dim_title dt
WHERE dt.title_type_name = 'movie'
  AND EXISTS (
      SELECT 1 FROM staged_analytics.fact_title_genre_flat
      WHERE title_id = dt.title_id AND genre_name = 'Action'
  )
  AND EXISTS (
      SELECT 1 FROM staged_analytics.fact_title_genre_flat
      WHERE title_id = dt.title_id AND genre_name = 'Adventure'
  )
ORDER BY dt.average_rating DESC;
```

---

## Q16 — Top 10 movies by rating released in the United States

```sql
SELECT
    dt.title_id,
    dt.primary_title,
    dt.release_year,
    dt.average_rating,
    dt.number_of_votes
FROM staged_analytics.fact_title_release ftr
JOIN staged_analytics.dim_title dt ON ftr.title_id = dt.title_id
WHERE ftr.region_name = 'United States'
  AND dt.title_type_name = 'movie'
  AND dt.number_of_votes > 0
ORDER BY dt.average_rating DESC
LIMIT 10;
```

---

## Q17 — For each genre, number of movies with a rating below 5

```sql
SELECT
    genre_name,
    COUNT(DISTINCT title_id) AS low_rated_movie_count
FROM staged_analytics.fact_title_genre_flat
WHERE title_type_name = 'movie'
  AND average_rating > 0
  AND average_rating < 5
GROUP BY genre_name
ORDER BY low_rated_movie_count DESC;
```

---

## Q18 — All movies with average rating above 8 and at least 10,000 votes

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating,
    number_of_votes
FROM staged_analytics.dim_title
WHERE title_type_name = 'movie'
  AND average_rating > 8
  AND number_of_votes >= 10000
ORDER BY average_rating DESC;
```

---

## Q19 — Top 10 Comedy movies released between 2010 and 2020 by rating

```sql
SELECT
    ftg.title_id,
    dt.primary_title,
    dt.release_year,
    dt.average_rating,
    dt.number_of_votes
FROM staged_analytics.fact_title_genre_flat ftg
JOIN staged_analytics.dim_title dt ON ftg.title_id = dt.title_id
WHERE ftg.genre_name = 'Comedy'
  AND ftg.title_type_name = 'movie'
  AND ftg.release_year BETWEEN 2010 AND 2020
  AND dt.number_of_votes > 0
ORDER BY dt.average_rating DESC
LIMIT 10;
```

---

## Q20 — For each year, number of new titles and their average rating

```sql
SELECT
    release_year,
    COUNT(*)                       AS title_count,
    ROUND(AVG(average_rating), 2)  AS avg_rating
FROM staged_analytics.dim_title
WHERE release_year IS NOT NULL
GROUP BY release_year
ORDER BY release_year;
```

---

## Q21 — Top 5 actors by average movie rating in the last 5 years (leading role, min 5 movies)

> "Leading role" is defined as role_name IN ('actor', 'actress').
> Last 5 years = release_year >= 2021.

```sql
WITH actor_stats AS (
    SELECT
        fcc.person_id,
        dp.name,
        COUNT(DISTINCT fcc.title_id)      AS movie_count,
        ROUND(AVG(fcc.average_rating), 2) AS avg_rating
    FROM staged_analytics.fact_title_cast_crew fcc
    JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
    WHERE fcc.role_name IN ('actor', 'actress')
      AND fcc.release_year >= 2021
      AND fcc.average_rating > 0
    GROUP BY fcc.person_id, dp.name
    HAVING COUNT(DISTINCT fcc.title_id) >= 5
)
SELECT
    person_id,
    name,
    movie_count,
    avg_rating
FROM actor_stats
ORDER BY avg_rating DESC
LIMIT 5;
```

---

## Q22 — For each genre, top 3 movies by rating released in the last 10 years

```sql
WITH ranked AS (
    SELECT
        ftg.genre_name,
        ftg.title_id,
        dt.primary_title,
        dt.release_year,
        dt.average_rating,
        ROW_NUMBER() OVER (
            PARTITION BY ftg.genre_name
            ORDER BY dt.average_rating DESC
        ) AS rn
    FROM staged_analytics.fact_title_genre_flat ftg
    JOIN staged_analytics.dim_title dt ON ftg.title_id = dt.title_id
    WHERE ftg.title_type_name = 'movie'
      AND ftg.release_year >= 2015
      AND dt.number_of_votes > 0
)
SELECT genre_name, title_id, primary_title, release_year, average_rating
FROM ranked
WHERE rn <= 3
ORDER BY genre_name, rn;
```

---

## Q23 — Directors with highest average rating (min 10 movies)

```sql
WITH director_stats AS (
    SELECT
        fcc.person_id,
        dp.name,
        COUNT(DISTINCT fcc.title_id)      AS movie_count,
        ROUND(AVG(fcc.average_rating), 2) AS avg_rating
    FROM staged_analytics.fact_title_cast_crew fcc
    JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
    WHERE fcc.role_name = 'director'
      AND fcc.average_rating > 0
    GROUP BY fcc.person_id, dp.name
    HAVING COUNT(DISTINCT fcc.title_id) >= 10
)
SELECT
    person_id,
    name,
    movie_count,
    avg_rating
FROM director_stats
ORDER BY avg_rating DESC
LIMIT 20;
```

---

## Q24 — For each year in the last 20 years, the genre with the highest average rating

```sql
WITH genre_year_avg AS (
    SELECT
        release_year,
        genre_name,
        ROUND(AVG(average_rating), 2) AS avg_rating
    FROM staged_analytics.fact_title_genre_flat
    WHERE title_type_name = 'movie'
      AND release_year >= 2005
      AND average_rating > 0
    GROUP BY release_year, genre_name
),
ranked AS (
    SELECT
        release_year,
        genre_name,
        avg_rating,
        ROW_NUMBER() OVER (PARTITION BY release_year ORDER BY avg_rating DESC) AS rn
    FROM genre_year_avg
)
SELECT release_year, genre_name, avg_rating
FROM ranked
WHERE rn = 1
ORDER BY release_year;
```

---

## Q25 — Top 10 actors by total number of votes across all movies

```sql
SELECT
    fcc.person_id,
    dp.name,
    COUNT(DISTINCT fcc.title_id)  AS movie_count,
    SUM(fcc.number_of_votes)      AS total_votes
FROM staged_analytics.fact_title_cast_crew fcc
JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
WHERE fcc.role_name IN ('actor', 'actress')
GROUP BY fcc.person_id, dp.name
ORDER BY total_votes DESC
LIMIT 10;
```

---

## Q26 — Genres where adult content share exceeds 20%

```sql
SELECT
    genre_name,
    COUNT(*)                                                        AS total_movies,
    SUM(CASE WHEN is_adult = TRUE THEN 1 ELSE 0 END)               AS adult_movies,
    ROUND(
        100.0 * SUM(CASE WHEN is_adult = TRUE THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                               AS adult_share_pct
FROM staged_analytics.fact_title_genre_flat
WHERE title_type_name = 'movie'
GROUP BY genre_name
HAVING (100.0 * SUM(CASE WHEN is_adult = TRUE THEN 1 ELSE 0 END) / COUNT(*)) > 20
ORDER BY adult_share_pct DESC;
```

---

## Q27 — Movies featuring both 'Leonardo DiCaprio' and 'Kate Winslet'

```sql
WITH dicaprio AS (
    SELECT fcc.title_id
    FROM staged_analytics.fact_title_cast_crew fcc
    JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
    WHERE dp.name = 'Leonardo DiCaprio'
),
winslet AS (
    SELECT fcc.title_id
    FROM staged_analytics.fact_title_cast_crew fcc
    JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
    WHERE dp.name = 'Kate Winslet'
)
SELECT
    dt.title_id,
    dt.primary_title,
    dt.release_year
FROM staged_analytics.dim_title dt
JOIN dicaprio d ON dt.title_id = d.title_id
JOIN winslet  w ON dt.title_id = w.title_id
ORDER BY dt.release_year;
```

---

## Q28 — Actors with at least 5 movies before 2000 AND at least 5 movies after 2000

```sql
WITH actor_periods AS (
    SELECT
        fcc.person_id,
        dp.name,
        SUM(CASE WHEN fcc.release_year < 2000 THEN 1 ELSE 0 END)  AS movies_before_2000,
        SUM(CASE WHEN fcc.release_year >= 2000 THEN 1 ELSE 0 END) AS movies_after_2000
    FROM staged_analytics.fact_title_cast_crew fcc
    JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
    WHERE fcc.role_name IN ('actor', 'actress')
      AND fcc.release_year IS NOT NULL
    GROUP BY fcc.person_id, dp.name
)
SELECT
    person_id,
    name,
    movies_before_2000,
    movies_after_2000
FROM actor_periods
WHERE movies_before_2000 >= 5
  AND movies_after_2000 >= 5
ORDER BY movies_before_2000 + movies_after_2000 DESC;
```

---

## Q29 — Top 10 movies that improved the most vs the average rating in their year+genre

```sql
WITH genre_year_avg AS (
    SELECT
        genre_name,
        release_year,
        AVG(average_rating) AS genre_year_avg_rating
    FROM staged_analytics.fact_title_genre_flat
    WHERE title_type_name = 'movie'
      AND average_rating > 0
      AND release_year IS NOT NULL
    GROUP BY genre_name, release_year
),
title_vs_avg AS (
    SELECT
        ftg.title_id,
        dt.primary_title,
        ftg.genre_name,
        ftg.release_year,
        dt.average_rating,
        gya.genre_year_avg_rating,
        (dt.average_rating - gya.genre_year_avg_rating) AS rating_improvement
    FROM staged_analytics.fact_title_genre_flat ftg
    JOIN staged_analytics.dim_title dt ON ftg.title_id = dt.title_id
    JOIN genre_year_avg gya
        ON ftg.genre_name = gya.genre_name
       AND ftg.release_year = gya.release_year
    WHERE ftg.title_type_name = 'movie'
      AND dt.number_of_votes > 0
)
SELECT
    title_id,
    primary_title,
    genre_name,
    release_year,
    ROUND(average_rating, 2)          AS rating,
    ROUND(genre_year_avg_rating, 2)   AS genre_year_avg,
    ROUND(rating_improvement, 2)      AS improvement
FROM title_vs_avg
ORDER BY rating_improvement DESC
LIMIT 10;
```

---

## Q30 — For each of the last 5 years, top 3 directors by average rating (min 3 movies that year)

```sql
WITH director_year_stats AS (
    SELECT
        fcc.release_year,
        fcc.person_id,
        dp.name,
        COUNT(DISTINCT fcc.title_id)      AS movie_count,
        ROUND(AVG(fcc.average_rating), 2) AS avg_rating
    FROM staged_analytics.fact_title_cast_crew fcc
    JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
    WHERE fcc.role_name = 'director'
      AND fcc.release_year >= 2020
      AND fcc.average_rating > 0
    GROUP BY fcc.release_year, fcc.person_id, dp.name
    HAVING COUNT(DISTINCT fcc.title_id) >= 3
),
ranked AS (
    SELECT
        release_year,
        person_id,
        name,
        movie_count,
        avg_rating,
        ROW_NUMBER() OVER (PARTITION BY release_year ORDER BY avg_rating DESC) AS rn
    FROM director_year_stats
)
SELECT release_year, person_id, name, movie_count, avg_rating
FROM ranked
WHERE rn <= 3
ORDER BY release_year DESC, rn;
```

---

## Series & Episodes

---

## Q31 — Top 10 highest-rated TV series of all time (min 1,000 votes)

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating,
    number_of_votes
FROM staged_analytics.dim_title
WHERE title_type_name IN ('tvSeries', 'tvMiniSeries')
  AND number_of_votes >= 1000
ORDER BY average_rating DESC
LIMIT 10;
```

---

## Q32 — All episodes of 'Breaking Bad' ordered by season and episode number

```sql
SELECT
    fe.season_number,
    fe.episode_number,
    fe.episode_primary_title,
    fe.episode_release_year,
    fe.episode_average_rating,
    fe.episode_number_of_votes
FROM staged_analytics.fact_episode fe
WHERE fe.series_primary_title = 'Breaking Bad'
ORDER BY fe.season_number, fe.episode_number;
```

---

## Q33 — Highest-rated episode for each TV series (min 100 votes)

```sql
WITH ranked AS (
    SELECT
        series_title_id,
        series_primary_title,
        episode_title_id,
        episode_primary_title,
        season_number,
        episode_number,
        episode_average_rating,
        episode_number_of_votes,
        ROW_NUMBER() OVER (
            PARTITION BY series_title_id
            ORDER BY episode_average_rating DESC
        ) AS rn
    FROM staged_analytics.fact_episode
    WHERE episode_number_of_votes >= 100
)
SELECT
    series_title_id,
    series_primary_title,
    episode_title_id,
    episode_primary_title,
    season_number,
    episode_number,
    episode_average_rating,
    episode_number_of_votes
FROM ranked
WHERE rn = 1
ORDER BY episode_average_rating DESC;
```

---

## Q34 — Number of seasons and episodes per TV series

```sql
SELECT
    series_title_id,
    series_primary_title,
    COUNT(DISTINCT season_number)  AS season_count,
    COUNT(episode_title_id)        AS episode_count
FROM staged_analytics.fact_episode
WHERE season_number IS NOT NULL
GROUP BY series_title_id, series_primary_title
ORDER BY episode_count DESC;
```

---

## Q35 — All TV series with more than 5 seasons

```sql
SELECT
    series_title_id,
    series_primary_title,
    COUNT(DISTINCT season_number) AS season_count,
    COUNT(episode_title_id)       AS episode_count
FROM staged_analytics.fact_episode
WHERE season_number IS NOT NULL
GROUP BY series_title_id, series_primary_title
HAVING COUNT(DISTINCT season_number) > 5
ORDER BY season_count DESC;
```

---

## Q36 — Average episode rating per season for a specific series (e.g. 'Game of Thrones')

```sql
SELECT
    season_number,
    COUNT(episode_title_id)                      AS episode_count,
    ROUND(AVG(episode_average_rating), 2)        AS avg_episode_rating,
    SUM(episode_number_of_votes)                 AS total_votes
FROM staged_analytics.fact_episode
WHERE series_primary_title = 'Game of Thrones'
  AND season_number IS NOT NULL
  AND episode_number_of_votes > 0
GROUP BY season_number
ORDER BY season_number;
```

---

## Q37 — Top 10 TV series by total episode count

```sql
SELECT
    series_title_id,
    series_primary_title,
    COUNT(episode_title_id)       AS episode_count,
    COUNT(DISTINCT season_number) AS season_count
FROM staged_analytics.fact_episode
GROUP BY series_title_id, series_primary_title
ORDER BY episode_count DESC
LIMIT 10;
```

---

## Q38 — For each genre, the highest-rated TV series

```sql
WITH ranked AS (
    SELECT
        ftg.genre_name,
        dt.title_id,
        dt.primary_title,
        dt.release_year,
        dt.average_rating,
        dt.number_of_votes,
        ROW_NUMBER() OVER (
            PARTITION BY ftg.genre_name
            ORDER BY dt.average_rating DESC
        ) AS rn
    FROM staged_analytics.fact_title_genre_flat ftg
    JOIN staged_analytics.dim_title dt ON ftg.title_id = dt.title_id
    WHERE ftg.title_type_name IN ('tvSeries', 'tvMiniSeries')
      AND dt.number_of_votes >= 1000
)
SELECT genre_name, title_id, primary_title, release_year, average_rating, number_of_votes
FROM ranked
WHERE rn = 1
ORDER BY genre_name;
```

---

## Q39 — Top-rated TV miniseries (tvMiniSeries) with at least 500 votes

```sql
SELECT
    title_id,
    primary_title,
    release_year,
    average_rating,
    number_of_votes
FROM staged_analytics.dim_title
WHERE title_type_name = 'tvMiniSeries'
  AND number_of_votes >= 500
ORDER BY average_rating DESC
LIMIT 20;
```

---

## Q40 — Actors who appeared in both movies and TV series

```sql
SELECT
    fcc.person_id,
    dp.name,
    COUNT(DISTINCT CASE WHEN dt.title_type_name = 'movie'    THEN fcc.title_id END) AS movie_count,
    COUNT(DISTINCT CASE WHEN dt.title_type_name = 'tvSeries' THEN fcc.title_id END) AS series_count
FROM staged_analytics.fact_title_cast_crew fcc
JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
JOIN staged_analytics.dim_title  dt ON fcc.title_id  = dt.title_id
WHERE fcc.role_name IN ('actor', 'actress')
  AND dt.title_type_name IN ('movie', 'tvSeries')
GROUP BY fcc.person_id, dp.name
HAVING COUNT(DISTINCT CASE WHEN dt.title_type_name = 'movie'    THEN fcc.title_id END) >= 1
   AND COUNT(DISTINCT CASE WHEN dt.title_type_name = 'tvSeries' THEN fcc.title_id END) >= 1
ORDER BY movie_count + series_count DESC
LIMIT 20;
```

---

## Q41 — TV series whose average episode rating improved from season 1 to the last season

```sql
WITH season_avg AS (
    SELECT
        series_title_id,
        series_primary_title,
        season_number,
        ROUND(AVG(episode_average_rating), 2) AS avg_rating,
        MAX(season_number) OVER (PARTITION BY series_title_id) AS max_season
    FROM staged_analytics.fact_episode
    WHERE season_number IS NOT NULL
      AND episode_number_of_votes > 0
    GROUP BY series_title_id, series_primary_title, season_number
),
first_and_last AS (
    SELECT
        series_title_id,
        series_primary_title,
        MAX(CASE WHEN season_number = 1            THEN avg_rating END) AS season_1_avg,
        MAX(CASE WHEN season_number = max_season   THEN avg_rating END) AS last_season_avg
    FROM season_avg
    WHERE season_number = 1 OR season_number = max_season
    GROUP BY series_title_id, series_primary_title
)
SELECT
    series_title_id,
    series_primary_title,
    season_1_avg,
    last_season_avg,
    ROUND(last_season_avg - season_1_avg, 2) AS rating_improvement
FROM first_and_last
WHERE season_1_avg IS NOT NULL
  AND last_season_avg IS NOT NULL
  AND last_season_avg > season_1_avg
ORDER BY rating_improvement DESC
LIMIT 20;
```

---

## Q42 — For each year, how many new TV series premiered

```sql
SELECT
    release_year,
    COUNT(*) AS new_series_count
FROM staged_analytics.dim_title
WHERE title_type_name IN ('tvSeries', 'tvMiniSeries')
  AND release_year IS NOT NULL
GROUP BY release_year
ORDER BY release_year;
```

---

## Q43 — Top 5 directors who have directed the most TV episodes

```sql
SELECT
    fcc.person_id,
    dp.name,
    COUNT(DISTINCT fcc.title_id) AS episodes_directed
FROM staged_analytics.fact_title_cast_crew fcc
JOIN staged_analytics.dim_person dp ON fcc.person_id = dp.person_id
JOIN staged_analytics.dim_title  dt ON fcc.title_id  = dt.title_id
WHERE fcc.role_name = 'director'
  AND dt.title_type_name = 'tvEpisode'
GROUP BY fcc.person_id, dp.name
ORDER BY episodes_directed DESC
LIMIT 5;
```

---

## Q44 — Top 10 best-rated individual episodes across all TV series (min 1,000 votes)

```sql
SELECT
    fe.series_primary_title,
    fe.season_number,
    fe.episode_number,
    fe.episode_primary_title,
    fe.episode_average_rating,
    fe.episode_number_of_votes
FROM staged_analytics.fact_episode fe
WHERE fe.episode_number_of_votes >= 1000
ORDER BY fe.episode_average_rating DESC
LIMIT 10;
```

---

## Q45 — For each TV series, the season with the highest average episode rating

```sql
WITH season_avg AS (
    SELECT
        series_title_id,
        series_primary_title,
        season_number,
        ROUND(AVG(episode_average_rating), 2) AS avg_season_rating,
        COUNT(episode_title_id)               AS episode_count
    FROM staged_analytics.fact_episode
    WHERE season_number IS NOT NULL
      AND episode_number_of_votes > 0
    GROUP BY series_title_id, series_primary_title, season_number
),
ranked AS (
    SELECT
        series_title_id,
        series_primary_title,
        season_number,
        avg_season_rating,
        episode_count,
        ROW_NUMBER() OVER (
            PARTITION BY series_title_id
            ORDER BY avg_season_rating DESC
        ) AS rn
    FROM season_avg
)
SELECT
    series_title_id,
    series_primary_title,
    season_number      AS best_season,
    avg_season_rating,
    episode_count
FROM ranked
WHERE rn = 1
ORDER BY avg_season_rating DESC;
```
