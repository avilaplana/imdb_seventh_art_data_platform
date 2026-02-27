# 50 SQL Questions for Silver Layer Data Model

This document contains 50 challenging SQL questions designed to test advanced SQL skills on the **complete silver layer Entity-Relationship (ER) data model**. These questions cover all tables and relationships in the silver layer schema, including:

- **Core entities**: `title`, `person`, `role`, `genre`, `title_type`, `region`, `language`, `attribute`
- **Junction tables**: `genre_title`, `title_person_role`, `role_person`
- **Hierarchical structures**: `title_episode` (series and episodes)
- **Localization**: `title_localized` (multi-language and multi-region support)

These questions are suitable for practice exercises and can be used in a RAG system for AI-powered SQL generation.

## Table of Contents
1. [Complex Joins and Relationships](#complex-joins-and-relationships)
2. [Window Functions and Analytics](#window-functions-and-analytics)
3. [Aggregations and Grouping](#aggregations-and-grouping)
4. [Subqueries and CTEs](#subqueries-and-ctes)
5. [Time-Based Analysis](#time-based-analysis)
6. [Statistical and Ranking Queries](#statistical-and-ranking-queries)
7. [Multi-Dimensional Analysis](#multi-dimensional-analysis)
8. [Pattern Matching and Text Analysis](#pattern-matching-and-text-analysis)
9. [Recursive and Hierarchical Queries](#recursive-and-hierarchical-queries)
10. [Advanced Business Logic](#advanced-business-logic)

---

## Complex Joins and Relationships

### Question 1: Multi-Table Join with Filtering
Find all titles that have at least 3 different genres, include the title name, release year, average rating, and list all genres associated with each title. Only include titles released after 2010 with an average rating above 7.0.

**Expected Output Columns:** title_id, primary_title, release_year, average_rating, genre_list (comma-separated)

**Difficulty:** ⭐⭐⭐⭐

**Solution:**

```sql
SELECT
	t.title_id,
	t.primary_title,
	t.release_year,
	t.average_rating,
	concat_ws(', ', sort_array(collect_list(g.genre_name)))  AS genre_list
FROM demo.silver.title t
JOIN demo.silver.genre_title gt
ON t.title_id = gt.title_id
JOIN demo.silver.genre g
ON gt.genre_id = g.genre_id
WHERE t.release_year > 2010 and t.average_rating > 7.0
GROUP BY t.title_id, t.primary_title, t.release_year, t.average_rating
HAVING COUNT(*) > 2
ORDER BY release_year, average_rating
```


---

### Question 2: Complex Many-to-Many Relationships
For each person who has worked in at least 5 different titles, find their most common role (by count), the total number of titles they've worked on, and the average rating of all titles they've been involved in. Include only people who have worked in titles with at least 1000 votes.

**Expected Output Columns:** person_id, name, most_common_role, total_titles, avg_title_rating

**Difficulty:** ⭐⭐⭐⭐⭐

**Solution:**

```sql
WITH person_id_with_min_votes AS (
	SELECT
		p.person_id,
		p.name,
		MIN(t.number_of_votes) AS min_number_of_votes
	FROM demo.silver.person p
	JOIN demo.silver.title_person_role tpr
	ON p.person_id = tpr.person_id
	JOIN demo.silver.title t
	ON tpr.title_id = t.title_id
	GROUP BY p.person_id, p.name
),
person_and_role AS (
  SELECT
    tpr.person_id,
    r.role_name,
    COUNT(*) AS counter_role
  FROM demo.silver.title_person_role tpr
  JOIN demo.silver.role r
  ON tpr.role_id = r.role_id
  GROUP BY tpr.person_id, r.role_name
),
person_and_common_role_ranked AS (
  SELECT
    person_id,
    role_name,
    ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY counter_role DESC,role_name) AS row_number
    FROM person_and_role
    
), 
person_and_most_common_role AS (
	SELECT
		person_id,
    role_name
	FROM person_and_common_role_ranked
	WHERE row_number = 1
),
person_metrics AS (
  SELECT
    pmv.person_id,
    pmv.name,
    COUNT(*) AS total_titles,
    AVG(t.average_rating) AS avg_title_rating
  FROM person_id_with_min_votes pmv
  JOIN demo.silver.title_person_role tpr
  ON pmv.person_id = tpr.person_id
  JOIN demo.silver.title t
  ON tpr.title_id = t.title_id
  WHERE pmv.min_number_of_votes >= 1000
  GROUP BY pmv.person_id, pmv.name
  HAVING total_titles >= 5
)

SELECT
  pm.person_id,
  pm.name,
  pm.total_titles,
  pm.avg_title_rating,
  pcr.role_name AS most_common_role
FROM person_metrics pm
JOIN person_and_most_common_role pcr
ON pm.person_id = pcr.person_id
ORDER BY pm.avg_title_rating DESC
```

---

### Question 3: Self-Referential Join with Aggregation
Find all TV series (identified by having episodes) and for each series, calculate:
- Total number of episodes
- Average episode duration
- Average rating across all episodes
- The season with the highest average rating

**Expected Output Columns:** parent_title_id, series_title, total_episodes, avg_episode_duration, avg_series_rating, best_season_number, best_season_rating

**Difficulty:** ⭐⭐⭐⭐⭐

**Solution:**

WITH metrics_series_season AS (
	SELECT
		te.series_title_id AS series_id,
		te.season_number,
		ROUND(AVG(t.average_rating),2) AS avg_rating_season
	FROM demo.silver.title_episode te
	JOIN demo.silver.title t
	ON te.title_id = t.title_id
	GROUP BY te.series_title_id, te.season_number
),
metrics_best_season as (
	SELECT
		ranked.series_id,
		ranked.season_number AS best_season_number,
		ranked.avg_rating_season AS best_season_rating
	FROM
		(SELECT
			series_id,
			ROW_NUMBER() OVER (PARTITION BY series_id ORDER BY avg_rating_season DESC) AS row_number,
			avg_rating_season,
			season_number
		FROM metrics_series_season
		) AS ranked
	WHERE row_number = 1
),
metrics_series AS (
	SELECT
		t.title_id AS series_id,
		t.primary_title,
		COUNT(*) AS total_episodes,
		AVG(t.duration_minutes) AS avg_episode_duration,
		AVG(t.average_rating) AS avg_series_rating
	FROM demo.silver.title t
	JOIN demo.silver.title_type tp
	ON t.title_type_id = tp.title_type_id
	JOIN demo.silver.title_episode te
	ON t.title_id = te.series_title_id
	JOIN demo.silver.title t_episodes
	ON te.title_id = t_episodes.title_id
	WHERE tp.title_type_name = 'tvSeries'
	GROUP BY t.title_id, t.primary_title
)

SELECT
	ms.series_id,
	ms.primary_title AS series_title,
	ms.total_episodes,
	ms.avg_episode_duration,
	ms.avg_series_rating,
	mbs.best_season_number,
	mbs.best_season_rating
FROM metrics_best_season mbs
JOIN metrics_series ms
ON mbs.series_id = ms.series_id
ORDER BY avg_series_rating DESC , total_episodes DESC

---

### Question 4: Cross-Table Localization Analysis
For each title, find how many localized versions exist, and identify titles that have localized versions in at least 5 different languages but are missing localized versions in at least 2 specific regions (e.g., 'US' and 'UK'). Include the original title and all available language-region combinations.

**Expected Output Columns:** title_id, primary_title, total_localizations, missing_regions, available_localizations (JSON or array format)

**Difficulty:** ⭐⭐⭐⭐⭐

**Solution:**

```sql
WITH localization_base AS (
    -- One row per (title, language, region)
    SELECT
        tl.title_id,
        r.region_code,
        l.language_code
    FROM demo.silver.title_localized tl
    JOIN demo.silver.regions r
        ON tl.region_id = r.region_id
    JOIN demo.silver.languages l
        ON tl.language_id = l.language_id
),

title_agg AS (
    -- Aggregate localization info per title
    SELECT
        title_id,
        COUNT(DISTINCT language_code) AS total_localizations,
        COLLECT_SET(
            STRUCT(language_code, region_code)
        ) AS available_localizations,
        COLLECT_SET(region_code) AS available_regions
    FROM localization_base
    GROUP BY title_id
),

required_regions AS (
    -- Regions that must be checked for missing localizations
    SELECT ARRAY('US', 'UK') AS regions
),

with_missing_regions AS (
    -- Compute which required regions are missing per title
    SELECT
        ta.title_id,
        ta.total_localizations,
        ta.available_localizations,
        ARRAY_EXCEPT(rr.regions, ta.available_regions) AS missing_regions
    FROM title_agg ta
    CROSS JOIN required_regions rr
)

SELECT
    t.title_id,
    t.primary_title,
    wmr.total_localizations,
    wmr.missing_regions,
    wmr.available_localizations
FROM with_missing_regions wmr
JOIN demo.silver.title t
    ON wmr.title_id = t.title_id
WHERE wmr.total_localizations >= 5
  AND SIZE(wmr.missing_regions) >= 2
```

---

### Question 5: Multi-Level Relationship Traversal
Find all actors (role_name = 'actor') who have worked with at least 3 different directors (role_name = 'director') on titles that share at least one common genre. For each actor-director pair, show the number of titles they've collaborated on and the average rating of those titles.

**Expected Output Columns:** actor_id, actor_name, director_id, director_name, collaboration_count, avg_collaboration_rating, shared_genres

**Difficulty:** ⭐⭐⭐⭐⭐

**Solution:**

```sql
WITH actor_director_titles AS (
    SELECT
        a.person_id      AS actor_id,
        d.person_id      AS director_id,
        t.title_id,
        g.genre_name,
        t.average_rating
    FROM demo.silver.title_person_role a
    JOIN demo.silver.role ar
        ON a.role_id = ar.role_id
       AND ar.role_name = 'actor'
    JOIN demo.silver.title_person_role d
        ON a.title_id = d.title_id
    JOIN demo.silver.role dr
        ON d.role_id = dr.role_id
       AND dr.role_name = 'director'
    JOIN demo.silver.genre_title gt
        ON a.title_id = gt.title_id
    JOIN demo.silver.genre g
        ON gt.genre_id = g.genre_id
    JOIN demo.silver.title t
        ON a.title_id = t.title_id
),

qualified_actor_genres AS (
    SELECT
        actor_id,
        genre_name
    FROM actor_director_titles
    GROUP BY actor_id, genre_name
    HAVING COUNT(DISTINCT director_id) >= 3
)

SELECT
    ad.actor_id,
    pa.name AS actor_name,
    ad.director_id,
    pd.name AS director_name,
    COUNT(DISTINCT ad.title_id) AS collaboration_count,
    ROUND(AVG(ad.average_rating), 2) AS avg_collaboration_rating,
    COLLECT_SET(ad.genre_name) AS shared_genres
FROM actor_director_titles ad
JOIN qualified_actor_genres q
    ON ad.actor_id = q.actor_id
   AND ad.genre_name = q.genre_name
JOIN demo.silver.person pa
    ON ad.actor_id = pa.person_id
JOIN demo.silver.person pd
    ON ad.director_id = pd.person_id
GROUP BY
    ad.actor_id,
    pa.name,
    ad.director_id,
    pd.name
ORDER BY
    ad.actor_id,
    ad.director_id
```
---

## Window Functions and Analytics

### Question 6: Ranking with Partitioning
For each genre, rank all titles by their average rating (considering only titles with at least 100 votes), and identify the top 3 titles per genre. Also calculate the percentile rank of each title within its genre.

**Expected Output Columns:** genre_name, title_id, primary_title, average_rating, genre_rank, percentile_rank

**Difficulty:** ⭐⭐⭐⭐

**Solution:**

```sql
WITH genre_rank AS (
	SELECT 
		g.genre_name,
		t.title_id, 
		t.primary_title, 
		t.average_rating,
		ROW_NUMBER() OVER (PARTITION BY g.genre_name ORDER BY t.average_rating DESC) AS genre_rank,
		PERCENT_RANK() OVER (PARTITION BY g.genre_name ORDER BY t.average_rating DESC) AS percentile_rank
	FROM demo.silver.title t
	JOIN demo.silver.genre_title tg
	ON t.title_id = tg.title_id
	JOIN demo.silver.genre g
	ON tg.genre_id = g.genre_id
	WHERE t.number_of_votes >= 100
	ORDER BY g.genre_name
)

SELECT 
	* 
FROM genre_rank
WHERE genre_rank <= 3
```

---

### Question 7: Running Totals and Moving Averages
Calculate a 5-year moving average of the average rating for titles released each year, grouped by title_type. Also show the running total of titles released and the cumulative average rating up to each year.

**Expected Output Columns:** release_year, title_type_name, titles_released, avg_rating, running_total_titles, cumulative_avg_rating, moving_avg_5yr

**Difficulty:** ⭐⭐⭐⭐⭐

**Solution:**

```sql
WITH title_type_year_grouped AS (	
    SELECT 
        t.release_year,
        tt.title_type_name,
        COUNT(*) AS titles_released,
        AVG(t.average_rating) AS avg_rating
    FROM demo.silver.title t
    JOIN demo.silver.title_type tt
      ON t.title_type_id = tt.title_type_id
    WHERE t.release_year IS NOT NULL
    GROUP BY tt.title_type_name, t.release_year
)

SELECT
    release_year,
    title_type_name,
    titles_released,
    avg_rating,

    -- running total of titles released
    SUM(titles_released) OVER (
        PARTITION BY title_type_name
        ORDER BY release_year
    ) AS running_total_titles,

    -- cumulative (weighted) average rating
    SUM(avg_rating * titles_released) OVER (
        PARTITION BY title_type_name
        ORDER BY release_year
    )
    /
    SUM(titles_released) OVER (
        PARTITION BY title_type_name
        ORDER BY release_year
    ) AS cumulative_avg_rating,

    -- 5-year moving average of yearly avg ratings
    AVG(avg_rating) OVER (
        PARTITION BY title_type_name
        ORDER BY release_year
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS moving_avg_5yr

FROM title_type_year_grouped
ORDER BY title_type_name, release_year
```

---

### Question 8: Lead/Lag Analysis
For each person, find their career progression by identifying the year they first appeared in a title, the year of their most recent appearance, and calculate the year-over-year change in the number of titles they worked on. Include a flag indicating if their career is still active (worked on a title in the last 3 years).

**Expected Output Columns:** person_id, name, first_appearance_year, last_appearance_year, total_years_active, titles_per_year_change, is_active

**Difficulty:** ⭐⭐⭐⭐

**Solution:**

```sql
WITH person_general_metric AS (
    SELECT 
        p.person_id,
        p.name,
        MIN(t.release_year) AS first_appearance_year,
        MAX(t.release_year) AS last_appearance_year,
        MAX(t.release_year) - MIN(t.release_year) + 1 AS total_years_active,
        CASE 
            WHEN MAX(t.release_year) >= YEAR(CURDATE()) - 2 THEN 1
            ELSE 0
        END AS is_active
    FROM demo.silver.person p
    JOIN demo.silver.title_person_role tpr 
        ON p.person_id = tpr.person_id
    JOIN demo.silver.title t 
        ON tpr.title_id = t.title_id
    WHERE t.release_year IS NOT NULL
    GROUP BY p.person_id, p.name
),

person_title_year_metric AS (
    SELECT 
        p.person_id, 
        t.release_year,
        COUNT(DISTINCT t.title_id) AS titles_per_year
    FROM demo.silver.person p
    JOIN demo.silver.title_person_role tpr 
        ON p.person_id = tpr.person_id
    JOIN demo.silver.title t 
        ON tpr.title_id = t.title_id
    WHERE t.release_year IS NOT NULL
    GROUP BY p.person_id, t.release_year
),

title_year_change_metric AS (
    SELECT 
        person_id,
        release_year,
        titles_per_year
            - LAG(titles_per_year) OVER (
                PARTITION BY person_id 
                ORDER BY release_year
              ) AS titles_per_year_change
    FROM person_title_year_metric
),

latest_year_change AS (
    SELECT *
    FROM (
        SELECT 
            person_id,
            titles_per_year_change,
            ROW_NUMBER() OVER (
                PARTITION BY person_id 
                ORDER BY release_year DESC
            ) AS rn
        FROM title_year_change_metric
    ) x
    WHERE rn = 1
)

SELECT 
    pgm.person_id,
    pgm.name,
    pgm.first_appearance_year,
    pgm.last_appearance_year,
    pgm.total_years_active,
    lyc.titles_per_year_change,
    pgm.is_active
FROM person_general_metric pgm
LEFT JOIN latest_year_change lyc
    ON pgm.person_id = lyc.person_id
ORDER BY pgm.person_id
```

---

### Question 9: Window Functions with Multiple Partitions
For each title, calculate:
- The rank of its rating within its release year
- The rank of its rating within its genre (considering all genres of the title)
- The difference between its rating and the median rating of its title_type
- The number of standard deviations its rating is from the mean rating of its release year

**Expected Output Columns:** title_id, primary_title, release_year, average_rating, year_rank, genre_rank, rating_vs_type_median, rating_z_score

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 10: First/Last Value Analysis
For each TV series, find the first and last episode (by season_number and episode_number), their ratings, and calculate the rating trend (improvement or decline) from first to last episode. Also identify episodes that represent rating peaks (highest rating in their season).

**Expected Output Columns:** parent_title_id, series_title, first_episode_id, first_episode_rating, last_episode_id, last_episode_rating, rating_trend, peak_episodes (array)

**Difficulty:** ⭐⭐⭐⭐⭐

---

## Aggregations and Grouping

### Question 11: Multi-Level Grouping with Filters
Group titles by title_type and release_year, then calculate:
- Count of titles
- Average rating (weighted by number_of_votes)
- Total votes across all titles
- Percentage of adult titles
- The most common genre combination (e.g., "Action, Adventure, Sci-Fi")

**Expected Output Columns:** title_type_name, release_year, title_count, weighted_avg_rating, total_votes, adult_percentage, most_common_genre_combo

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 12: Conditional Aggregations
For each person, calculate:
- Total number of titles as actor
- Total number of titles as director
- Total number of titles as writer
- Average rating of titles where they were actor
- Average rating of titles where they were director
- The role in which they achieved their highest average rating

**Expected Output Columns:** person_id, name, actor_count, director_count, writer_count, actor_avg_rating, director_avg_rating, best_role, best_role_rating

**Difficulty:** ⭐⭐⭐⭐

---

### Question 13: Pivot-Style Aggregation
Create a matrix showing, for each genre pair (e.g., Action-Comedy, Drama-Thriller), the number of titles that belong to both genres and their average rating. Only include genre pairs that appear together in at least 10 titles.

**Expected Output Columns:** genre_1, genre_2, co_occurrence_count, avg_rating

**Difficulty:** ⭐⭐⭐⭐

---

### Question 14: Grouping Sets and Rollups
Generate a comprehensive report with multiple levels of aggregation:
- Overall statistics (all titles)
- By title_type
- By release_year
- By title_type and release_year
- By genre
- By title_type and genre

For each level, show: count, average rating, min/max rating, total votes.

**Expected Output Columns:** grouping_level, title_type_name, release_year, genre_name, title_count, avg_rating, min_rating, max_rating, total_votes

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 15: Distinct Count with Conditions
Find all titles and count:
- How many unique actors appeared
- How many unique directors worked on it
- How many unique languages it's available in
- How many unique regions it's localized for
- The total number of unique people involved (across all roles)

**Expected Output Columns:** title_id, primary_title, unique_actors, unique_directors, unique_languages, unique_regions, total_unique_people

**Difficulty:** ⭐⭐⭐

---

## Subqueries and CTEs

### Question 16: Correlated Subquery with Multiple Conditions
Find titles that have a higher average rating than the average rating of all other titles released in the same year and belong to at least one of the same genres. Also ensure the title has more votes than 80% of titles in its primary genre.

**Expected Output Columns:** title_id, primary_title, release_year, average_rating, year_avg_rating, percentile_in_genre

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 17: Nested Subqueries with EXISTS
Identify people who have worked on titles in every genre that exists in the database. For each such person, list all genres they've worked in and the title with the highest rating in each genre.

**Expected Output Columns:** person_id, name, total_genres_covered, genre_details (JSON or structured format)

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 18: CTE Chain for Complex Logic
Using multiple CTEs, calculate:
1. Titles with above-average ratings for their release year
2. From those, titles that have actors who also appeared in at least 3 other high-rated titles
3. From those, titles that share at least 2 genres with other high-rated titles
4. Final output: these "elite" titles with their network of connected titles

**Expected Output Columns:** title_id, primary_title, release_year, average_rating, connected_titles_count, shared_genres_count

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 19: Recursive CTE for Career Paths
For each person, trace their career evolution by finding:
- Their first title (by release_year)
- All subsequent titles they worked on
- The progression of their average rating over time
- Identify career milestones (first title with rating > 8.0, first title with > 1M votes, etc.)

**Expected Output Columns:** person_id, name, career_timeline (structured data showing year, title, rating, milestone)

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 20: Subquery in SELECT with Aggregation
For each title, calculate:
- The percentage of its rating compared to the maximum rating in its release year
- The number of titles released in the same year that have a lower rating
- The rank of its number_of_votes among all titles in its primary genre
- A "popularity score" combining rating percentile and vote percentile

**Expected Output Columns:** title_id, primary_title, release_year, rating_percent_of_max, titles_beaten_in_year, vote_rank_in_genre, popularity_score

**Difficulty:** ⭐⭐⭐⭐

---

## Time-Based Analysis

### Question 21: Temporal Trends with Gaps
Analyze the release pattern of titles over time, identifying:
- Years with the highest and lowest number of releases
- 5-year periods with the best average ratings
- Trends in title duration over decades
- Identify "golden ages" for each title_type (periods with consistently high ratings)

**Expected Output Columns:** time_period, title_type_name, release_count, avg_rating, avg_duration, is_golden_age

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 22: Cohort Analysis
Group titles by their release decade and analyze:
- Average rating trends across decades
- Genre popularity shifts (which genres were most popular in each decade)
- Evolution of title duration
- Adult content percentage over time

**Expected Output Columns:** decade, title_count, avg_rating, top_genre, avg_duration, adult_percentage

**Difficulty:** ⭐⭐⭐⭐

---

### Question 23: Time-Series Gaps and Continuity
For TV series, identify:
- Series with gaps in episode releases (missing seasons or long breaks)
- Series with consistent release patterns
- Calculate the average time between seasons
- Identify series that started in one decade and are still active

**Expected Output Columns:** parent_title_id, series_title, first_season_year, last_season_year, total_seasons, avg_years_between_seasons, has_gaps, is_active

**Difficulty:** ⭐⭐⭐⭐

---

### Question 24: Person Career Timeline Analysis
For each person born before 1980, create a timeline showing:
- Their active years in the industry
- Peak performance years (years with highest average rating of titles)
- Career longevity (years between first and last title)
- Identify if they had a "comeback" (gap of 5+ years followed by new titles)

**Expected Output Columns:** person_id, name, birth_year, first_title_year, last_title_year, career_span_years, peak_years, has_comeback

**Difficulty:** ⭐⭐⭐⭐

---

### Question 25: Seasonal and Cyclical Patterns
Analyze if there are patterns in:
- Release months (if available) or release years
- Rating patterns by release year (do ratings follow cycles?)
- Genre popularity cycles
- Identify if certain genres perform better in certain time periods

**Expected Output Columns:** time_period, genre_name, release_count, avg_rating, trend_direction

**Difficulty:** ⭐⭐⭐⭐

---

## Statistical and Ranking Queries

### Question 26: Percentile and Quartile Analysis
For each title_type, calculate:
- Median rating
- 25th, 75th, and 90th percentile ratings
- Interquartile range
- Identify titles in the top 10% and bottom 10% of ratings
- Calculate z-scores for ratings within each title_type

**Expected Output Columns:** title_type_name, median_rating, p25_rating, p75_rating, p90_rating, iqr, title_id, rating_z_score, percentile_rank

**Difficulty:** ⭐⭐⭐⭐

---

### Question 27: Statistical Outliers
Identify statistical outliers in:
- Titles with ratings that are more than 2 standard deviations from the mean
- Titles with unusually high or low vote counts
- People with unusually long careers
- Genres with unusual rating distributions

For each outlier, provide context (what makes it an outlier).

**Expected Output Columns:** entity_type, entity_id, entity_name, metric, value, mean, std_dev, z_score, is_outlier

**Difficulty:** ⭐⭐⭐⭐

---

### Question 28: Ranking with Ties and Dense Ranking
Rank all titles by:
- Average rating (handle ties appropriately)
- Number of votes (using dense_rank)
- Combined score (rating * log(votes))
- Within each genre, rank titles
- Provide both rank and dense_rank for comparison

**Expected Output Columns:** title_id, primary_title, rating_rank, rating_dense_rank, vote_rank, combined_score_rank, genre_rank

**Difficulty:** ⭐⭐⭐

---

### Question 29: Top-N Per Group with Multiple Criteria
For each genre, find:
- Top 5 titles by rating (minimum 1000 votes)
- Top 5 titles by number of votes
- Top 5 titles by a combined metric (rating * sqrt(votes))
- Identify titles that appear in multiple top-5 lists

**Expected Output Columns:** genre_name, ranking_criteria, rank, title_id, primary_title, metric_value

**Difficulty:** ⭐⭐⭐⭐

---

### Question 30: Comparative Statistics
Compare statistics across different dimensions:
- Rating distribution by title_type vs. by genre
- Vote distribution by release_year vs. by title_type
- Calculate correlation-like metrics (e.g., do longer titles have higher ratings?)
- Identify which factors (duration, votes, release_year) best predict high ratings

**Expected Output Columns:** comparison_dimension, category, avg_rating, median_rating, std_dev_rating, correlation_with_duration, correlation_with_votes

**Difficulty:** ⭐⭐⭐⭐⭐

---

## Multi-Dimensional Analysis

### Question 31: Multi-Fact Table Analysis
Create a comprehensive analysis combining:
- Title ratings and votes
- Person involvement (count of people per role)
- Genre diversity (number of genres per title)
- Localization coverage (number of languages/regions)
- Episode count (for series)

Calculate a "completeness score" for each title based on these dimensions.

**Expected Output Columns:** title_id, primary_title, rating_score, involvement_score, genre_diversity_score, localization_score, completeness_score

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 32: Cross-Dimensional Filtering
Find titles that satisfy ALL of the following conditions:
- Released between 2010 and 2020
- Average rating > 7.5
- At least 10,000 votes
- Has at least 3 genres
- Available in at least 5 languages
- Has at least 5 actors
- Duration between 90 and 180 minutes (for movies) OR has at least 20 episodes (for series)

**Expected Output Columns:** title_id, primary_title, release_year, average_rating, number_of_votes, genre_count, language_count, actor_count, duration_or_episodes

**Difficulty:** ⭐⭐⭐

---

### Question 33: Dimension Hierarchies
Analyze the hierarchy: title_type → genre → title, and calculate:
- Average rating at each level
- Count of titles at each level
- Identify genre-title_type combinations with the highest average ratings
- Find the most "diverse" title_type (has titles in the most genres)

**Expected Output Columns:** title_type_name, genre_name, title_count, avg_rating, title_id, primary_title, average_rating

**Difficulty:** ⭐⭐⭐⭐

---

### Question 34: Multi-Table Aggregation
For each combination of title_type, genre, and release_year (where data exists), calculate:
- Total titles
- Average rating (weighted by votes)
- Total votes
- Most common language for localization
- Average number of people involved per title
- Percentage that are adult content

**Expected Output Columns:** title_type_name, genre_name, release_year, title_count, weighted_avg_rating, total_votes, most_common_language, avg_people_per_title, adult_percentage

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 35: Fact Table Enrichment
Enrich the title table with calculated dimensions:
- Genre count
- Language count
- Region count
- Actor count
- Director count
- Episode count (for series)
- Localization completeness (has original title flag = true)
- Collaboration network size (unique people worked with)

**Expected Output Columns:** All title columns plus: genre_count, language_count, region_count, actor_count, director_count, episode_count, has_original_localization, network_size

**Difficulty:** ⭐⭐⭐⭐

---

## Pattern Matching and Text Analysis

### Question 36: Title Pattern Analysis
Analyze title patterns:
- Titles that contain numbers
- Titles that are the same as their original_title
- Titles where primary_title differs significantly from original_title
- Calculate title length and see if it correlates with rating
- Find the most common words in high-rated titles (rating > 8.0)

**Expected Output Columns:** title_id, primary_title, original_title, title_length, is_same_as_original, contains_numbers, average_rating

**Difficulty:** ⭐⭐⭐

---

### Question 37: Localization Pattern Matching
For titles with multiple localizations:
- Find titles where the localized title is completely different from the original
- Identify patterns in how titles are translated (e.g., do certain regions consistently change titles?)
- Find titles that have the same localized name across multiple regions
- Calculate localization diversity (how different are the localized titles from each other?)

**Expected Output Columns:** title_id, primary_title, region_name, localized_title, is_different_from_original, localization_uniqueness_score

**Difficulty:** ⭐⭐⭐⭐

---

### Question 38: Person Name Analysis
Analyze person names:
- Find people with the same name (potential duplicates or name conflicts)
- Calculate average career length by name length (if name length correlates with success)
- Find the most common first names and last names in the database
- Identify people whose names appear in title names (e.g., actor name matches movie title)

**Expected Output Columns:** person_id, name, name_length, career_span, is_duplicate_name, appears_in_title_name

**Difficulty:** ⭐⭐⭐

---

### Question 39: Character Name Extraction
From the characters field in title_person, extract and analyze:
- Most common character names
- Character names that appear in multiple titles (same character across series?)
- Average number of characters per person per title
- Identify people who played the same character name in different titles

**Expected Output Columns:** person_id, name, character_name, title_count_with_character, is_recurring_character

**Difficulty:** ⭐⭐⭐⭐

---

### Question 40: Job Title Pattern Analysis
Analyze the job field in title_person and role_person:
- Most common job titles
- Job titles that correlate with higher-rated titles
- People who have held multiple different job titles
- Evolution of job titles over time (if temporal data available)

**Expected Output Columns:** job, frequency, avg_rating_when_used, person_count, is_common_job

**Difficulty:** ⭐⭐⭐

---

## Recursive and Hierarchical Queries

### Question 41: Series Episode Hierarchy
For each TV series, build a complete hierarchy:
- Series → Seasons → Episodes
- Calculate statistics at each level (average rating per season, per series)
- Identify the best and worst seasons
- Find episodes that are outliers (much higher or lower rating than series average)

**Expected Output Columns:** parent_title_id, series_title, season_number, episode_count, season_avg_rating, episode_id, episode_number, episode_rating, is_outlier

**Difficulty:** ⭐⭐⭐⭐

---

### Question 42: Genre Co-occurrence Network
Build a network of genres based on co-occurrence:
- For each genre, find its most common co-occurring genres
- Calculate a "genre similarity" score based on shared titles
- Identify genre clusters (groups of genres that often appear together)
- Find the "central" genre (appears with the most other genres)

**Expected Output Columns:** genre_name, co_occurring_genre, co_occurrence_count, similarity_score, cluster_id

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 43: Collaboration Network Depth
For a given person, find:
- All people they've directly worked with (1st degree)
- All people their collaborators have worked with (2nd degree)
- Calculate the "six degrees of separation" - shortest path to any other person
- Identify the most "connected" person (shortest average path to all others)

**Expected Output Columns:** person_id, name, first_degree_connections, second_degree_connections, avg_path_length_to_others, is_most_connected

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 44: Title Recommendation Network
Based on shared attributes, build a recommendation network:
- Titles that share at least 2 genres
- Titles that share at least 2 actors
- Titles that share the same director
- Titles released in the same year with similar ratings
- Calculate a "similarity score" combining all factors

**Expected Output Columns:** title_id_1, title_id_2, shared_genres, shared_actors, shared_director, similarity_score, recommendation_strength

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 45: Career Progression Tree
For people who started as actors and later became directors (or vice versa):
- Map their career progression
- Identify the transition point
- Compare their success in different roles
- Find people who successfully transitioned (higher ratings in new role)

**Expected Output Columns:** person_id, name, first_role, transition_year, second_role, first_role_avg_rating, second_role_avg_rating, is_successful_transition

**Difficulty:** ⭐⭐⭐⭐

---

## Advanced Business Logic

### Question 46: Content Quality Score
Create a composite "quality score" for each title combining:
- Normalized rating (0-1 scale)
- Normalized vote count (0-1 scale)
- Genre diversity score
- Localization coverage score
- People involvement score (number and variety of roles)
- Recency bonus (newer titles get slight boost)

Weight these factors appropriately and rank titles.

**Expected Output Columns:** title_id, primary_title, rating_score, vote_score, diversity_score, localization_score, involvement_score, recency_bonus, total_quality_score, quality_rank

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 47: Market Analysis
Perform market analysis:
- Identify underserved genres (genres with few titles but high average ratings)
- Find over-saturated genres (many titles, declining average ratings)
- Calculate genre "efficiency" (rating per title count)
- Predict which genres might be trending up or down

**Expected Output Columns:** genre_name, title_count, avg_rating, efficiency_score, trend_direction, market_status (underserved/oversaturated/balanced)

**Difficulty:** ⭐⭐⭐⭐

---

### Question 48: Talent Discovery Analysis
Identify "rising stars":
- People whose recent titles have higher ratings than their early titles
- People who worked on titles with increasing ratings over time
- People who transitioned from low-rated to high-rated titles
- Calculate a "momentum" score based on recent performance vs. career average

**Expected Output Columns:** person_id, name, career_avg_rating, recent_avg_rating, momentum_score, is_rising_star, best_recent_title

**Difficulty:** ⭐⭐⭐⭐

---

### Question 49: Content Gap Analysis
Identify content gaps:
- Genre-title_type combinations that don't exist but should (based on market demand)
- Regions that have few localized titles compared to others
- Time periods with fewer releases than expected
- People who haven't worked together but should (based on genre overlap)

**Expected Output Columns:** gap_type, gap_description, expected_count, actual_count, gap_size, recommendation

**Difficulty:** ⭐⭐⭐⭐⭐

---

### Question 50: Predictive Analytics Query
Build a query that predicts title success based on historical patterns:
- For titles with certain characteristics (genre, director, actors), predict likely rating range
- Identify "high-risk, high-reward" titles (unusual combinations that could succeed)
- Calculate success probability based on:
  - Director's historical performance
  - Actor's historical performance
  - Genre's historical performance
  - Similar titles' performance

**Expected Output Columns:** title_id, primary_title, predicted_rating_range, success_probability, risk_level, confidence_score, key_success_factors

**Difficulty:** ⭐⭐⭐⭐⭐

---

## Notes for RAG System Implementation

### Query Complexity Indicators
- ⭐⭐⭐ = Moderate complexity (3-5 table joins, basic aggregations)
- ⭐⭐⭐⭐ = High complexity (5-8 table joins, window functions, subqueries)
- ⭐⭐⭐⭐⭐ = Very high complexity (recursive CTEs, multiple CTEs, complex business logic)

### Expected Query Patterns
- Most questions require 3-8 table joins
- Window functions are common (RANK, DENSE_RANK, LAG, LEAD, PERCENTILE)
- CTEs are recommended for readability
- Aggregations often need GROUP BY with multiple columns
- Many questions benefit from JSON/array aggregation functions

### Database-Specific Considerations
- These queries are written for a generic SQL dialect
- For Spark SQL, use `collect_list` or `array_agg` for arrays
- For PostgreSQL, use `array_agg` or `jsonb_agg`
- Window functions syntax may vary slightly by database

### Testing Recommendations
1. Start with simpler questions (⭐⭐⭐) to validate schema understanding
2. Test with sample data to ensure queries return expected results
3. Verify performance on large datasets
4. Consider adding indexes on frequently joined columns
5. Use EXPLAIN ANALYZE to optimize query performance

---

## Usage in RAG System

When implementing these questions in a RAG system:

1. **Context Provision**: Include the ERD diagram and schema.yml in the context
2. **Question Categorization**: Tag questions by difficulty and topic
3. **Expected Output Format**: Define clear output schemas for each question
4. **Validation**: Create test cases with expected results
5. **Progressive Difficulty**: Allow users to filter by difficulty level
6. **Hints System**: Provide hints for very difficult questions (⭐⭐⭐⭐⭐)

---

*Generated for Seventh Art Analytics - Complete Silver Layer ER Data Model*
*Covers all tables and relationships in the silver layer schema*
*Last Updated: 2025*
