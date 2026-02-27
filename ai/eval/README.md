## NL to SQL - Evaluation strategy

I am building a data plaftorm in my local environment (OLLAMA) following the medallion architecture. I am implementing a Natural Language to SQL solution against the silver layer. Currently i have been some testing providing a database schema based on DBT models and a semantic layer. I am using the model `qwen2.5-coder:7b` with context size `16384`. My idea is to create a benchmark for local LLMs (~3 LLMS ) based on the following variables:

- **LLM**
- **Prompt**
- **Temperature/Top_p**
- **Database schema**
- **Semantic layer**
- **Windows context**

I have created **30 questions** classified in 3 groups:

## Easy

Single table, simple filters, no joins or aggregates.

1. “List the 10 highest‑rated movies released in 2020.”

2. “Show all movies released in 1999 with a rating of at least 8 out of 10.”

3. “Find the details of the movie titled ‘Inception’.”

4. “List all movies released after 2015 that are marked as adult content.”

5. “Show all movies that have a runtime longer than 150 minutes.”

6. “Find all titles released in Spain in the Spanish language.”

7. “List all movies that have no user rating yet.”

8. “Show all titles released in 2023 along with their primary title and release year.”

9. “List the first 20 titles in the catalog ordered by release year ascending.”

10. “Show all movies whose primary title contains the word ‘Star’.”

## Medium

2–3 tables, joins, simple aggregations, basic time filters.

1. “For each genre, what is the average rating of movies released after 2010?”

2. “List the top 10 highest‑rated action movies of all time.”

3. “For each year since 2000, how many movies were released?”

4. “Show the 20 most recent movies along with their average rating and number of votes.”

5. “List all movies that belong to both the ‘Action’ and ‘Adventure’ genres.”

6. “Find the top 10 movies by rating that were released in the United States.”

7. “For each genre, show the number of movies with a rating below 5.”

8. “List all movies with an average rating above 8 that have received at least 10,000 votes.”

9. “Show the top 10 ‘Comedy’ movies released between 2010 and 2020 by rating.”

10. “For each year, show the number of new titles and the average rating of those titles.”

## Hard

3+ tables, non‑trivial joins, semantics (“lead actor”, “recent years”), and more complex logic.

1. “Find the top 5 actors with the highest average movie rating in the last 5 years, considering only movies where they had a leading role and at least 5 such movies.”

2. “For each genre, list the top 3 movies by rating released in the last 10 years, including the movie title, year, genre, and rating.”

3. “Find the directors whose movies have the highest average rating, considering only directors with at least 10 movies.”

4. “For each year in the last 20 years, find the genre with the highest average rating and show that genre, the year, and the average rating.”

5. “Find the top 10 actors by total number of votes across all movies they have acted in.”

6. “For each genre, compute the share of movies that are adult content and show only genres where this share is above 20%.”

7. “Find all movies that feature both ‘Leonardo DiCaprio’ and ‘Kate Winslet’ and list their titles and release years.”

8. “For each actor, compute the number of movies they appeared in before 2000 and after 2000, and show only actors who have at least 5 movies in each period.”

9. “Find the top 10 movies that improved the most in rating compared to the average rating of movies released in the same year and genre.”

10. “For each of the last 5 years, list the top 3 directors by average rating of their movies in that year, considering only directors with at least 3 movies for that year.”


