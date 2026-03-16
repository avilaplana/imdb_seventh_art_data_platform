SELECT
	person_id,
	name, 
	birth_year, 
	death_year
FROM {{ ref('person') }}