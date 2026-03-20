{% macro promote_canonical_to_prod() %}

  {% set canonical_tables = [
    'regions',
    'languages',
    'genre_title',
    'genre',
    'person',
    'role_person',
    'role',
    'title_context',
    'title_episode',
    'title_localized',
    'title_person_role',
    'title_type',
    'title'
  ] %}

  {% call statement('create_prod_canonical_namespace') %}
    CREATE NAMESPACE IF NOT EXISTS demo.prod_canonical
  {% endcall %}

  {% for table in canonical_tables %}
    {{ log("Promoting stage_canonical." ~ table ~ " -> prod_canonical." ~ table, info=True) }}
    {% call statement('promote_canonical_' ~ table) %}
      CREATE OR REPLACE TABLE demo.prod_canonical.{{ table }} USING iceberg
      AS SELECT * FROM demo.stage_canonical.{{ table }}
    {% endcall %}
  {% endfor %}

{% endmacro %}
