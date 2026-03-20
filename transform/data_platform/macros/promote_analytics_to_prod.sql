{% macro promote_analytics_to_prod() %}

  {% set analytics_tables = [
    'dim_person',
    'dim_title',
    'fact_title_cast_crew',
    'fact_title_genre_flat',
    'fact_title_release',
    'fact_episode'
  ] %}

  {% call statement('create_prod_analytics_namespace') %}
    CREATE NAMESPACE IF NOT EXISTS demo.prod_analytics
  {% endcall %}

  {% for table in analytics_tables %}
    {{ log("Promoting stage_analytics." ~ table ~ " -> prod_analytics." ~ table, info=True) }}
    {% call statement('promote_analytics_' ~ table) %}
      CREATE OR REPLACE TABLE demo.prod_analytics.{{ table }} USING iceberg
      AS SELECT * FROM demo.stage_analytics.{{ table }}
    {% endcall %}
  {% endfor %}

{% endmacro %}
