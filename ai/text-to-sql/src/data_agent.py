from pathlib import Path
import json
import glob
from ollama import Client
import jaydebeapi

SPARK_THRIFT_HOST = "spark-thrift-server"
SPARK_THRIFT_PORT = 10000
DATABASE = "demo.silver"
LLM_MODEL = "qwen2.5-coder:7b"
SPARK_JARS = ":".join(glob.glob("/opt/bitnami/spark/jars/*.jar"))
MAX_RETRIES = 2

class Agent:
    def __init__(
        self,
        project_root: str = None,
        physical_schema_path: str = "physical_schema.json",
        semantic_layer_path: str = "semantic_layer.json",
    ):
        """
        project_root: optional base folder, default is the parent of this file
        schema paths are relative to project_root / 'data/'
        """
        # Resolve base folder
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent  # points to ai/text-to-sql/
        else:
            project_root = Path(project_root).resolve()

        data_folder = project_root / "data"
        self._physical_schema = self._load_schema(data_folder / physical_schema_path)
        self._semantic_layer = self._load_schema(data_folder / semantic_layer_path)

        # Connect to Spark
        self._spark_client = self._connect_to_spark()

        # LLM client
        self._llm_client = Client(host="http://host.docker.internal:11434")

    # -----------------------------
    # Public API
    # -----------------------------
    def infer(self, user_query: str) -> dict:
        """
        Returns a dictionary with:
        {
          "sql": "<generated SQL>",
          "result": {"columns": [...], "rows": [[...], ...]}
        }
        """
        history = []
        retry_count = 0

        # Generate SQL
        sql_query = self._generate_sql(user_query)

        # Retry loop if SQL fails
        while retry_count <= MAX_RETRIES:
            try:
                columns, rows = self._execute_sql(sql_query)
                return {"sql": sql_query, "result": {"columns": columns, "rows": rows}}
            except Exception as e:
                error = str(e)
                history.append({"sql": sql_query, "error": error})
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    raise RuntimeError(
                        f"Failed to execute SQL after {MAX_RETRIES} retries. Last error: {error}"
                    )
                sql_query = self._retry_sql(user_query, history)

    # -----------------------------
    # Internal methods
    # -----------------------------
    def _load_schema(self, path: str) -> dict:
        with open(path) as f:
            return json.load(f)

    def _connect_to_spark(self):
        return jaydebeapi.connect(
            "org.apache.hive.jdbc.HiveDriver",
            f"jdbc:hive2://{SPARK_THRIFT_HOST}:{SPARK_THRIFT_PORT}/{DATABASE}",
            ["dbt", ""],
            SPARK_JARS,
        )

    def _build_prompt(self, user_query: str) -> str:
        return f"""
You are a SQL expert. Generate Spark SQL based ONLY on the following database schema.
Do not hallucinate tables or columns. Use the semantic layer to interpret human-friendly terms.

Physical schema:
{json.dumps(self._physical_schema, indent=2)}

Semantic layer:
{json.dumps(self._semantic_layer, indent=2)}

User request:
{user_query}

Instructions:
- Only use tables and columns from the physical schema.
- Resolve enums, roles, languages, and canonical patterns using the semantic layer.
- Infer necessary joins automatically.
- Output valid SQL only.
- Do not include explanations or extra text.
- Enclose the SQL in triple backticks ```sql ... ```.

SQL:
"""

    def _generate_sql(self, user_query: str) -> str:
        prompt = self._build_prompt(user_query)
        response = self._llm_client.chat(
            model=LLM_MODEL, 
            messages=[{"role": "user", "content": prompt}],
            options={ "num_ctx": 16384 }
        )
        content_lines = response["message"]["content"].splitlines()
        if content_lines and "```sql" in content_lines[0]:
            sql_query = "\n".join(content_lines[1:-1])
        else:
            sql_query = "\n".join(content_lines)
        return sql_query.strip()

    def _execute_sql(self, sql_query: str):
        cursor = self._spark_client.cursor()
        cursor.execute(sql_query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return columns, rows

    def _retry_sql(self, user_query: str, history: list) -> str:
        context_prompt = f"User query: {user_query}\nPrevious attempts:\n{json.dumps(history, indent=2)}\n"
        context_prompt += "Please suggest a corrected Spark SQL query based on the schema."
        response = self._llm_client.chat(
            model=LLM_MODEL, messages=[{"role": "user", "content": context_prompt}]
        )
        return response["message"]["content"].strip()