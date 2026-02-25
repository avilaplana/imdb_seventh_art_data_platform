from pathlib import Path
import json
import glob
from ollama import Client
import jaydebeapi
from typing import List, Dict, Any

# -----------------------------
# Resources
# -----------------------------
SPARK_THRIFT_HOST = "spark-thrift-server"
SPARK_THRIFT_PORT = 10000
DATABASE = "demo.silver"
LLM_MODEL = "qwen2.5-coder:7b"
SPARK_JARS = ":".join(glob.glob("/opt/bitnami/spark/jars/*.jar"))

# load schemas once
DATA_FOLDER = Path(__file__).parent.parent.parent / "data"
PHYSICAL_SCHEMA = json.load(open(DATA_FOLDER / "physical_schema.json"))
SEMANTIC_LAYER = json.load(open(DATA_FOLDER / "semantic_layer.json"))

SPARK_CLIENT = jaydebeapi.connect(
    "org.apache.hive.jdbc.HiveDriver",
    f"jdbc:hive2://{SPARK_THRIFT_HOST}:{SPARK_THRIFT_PORT}/{DATABASE}",
    ["dbt", ""],
    SPARK_JARS,
)

LLM_CLIENT = Client(host="http://host.docker.internal:11434")

# -----------------------------
# Functions
# -----------------------------
def generate_sql(user_query: str) -> str:
    prompt = f"""
You are a SQL expert. Generate Spark SQL based ONLY on the following database schema.

Physical schema:
{json.dumps(PHYSICAL_SCHEMA, indent=2)}

Semantic layer:
{json.dumps(SEMANTIC_LAYER, indent=2)}

User request:
{user_query}

Instructions:
- Use only tables/columns from schema
- Resolve enums/roles using semantic layer
- Infer joins automatically
- Output ONLY valid Spark SQL
"""
    response = LLM_CLIENT.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 16384},
    )
    return response["message"]["content"].strip()


def execute_sql(sql: str) -> Dict[str, Any]:
    cursor = SPARK_CLIENT.cursor()
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return {"columns": columns, "rows": rows}


def retry_sql(user_query: str, history: List[Dict[str, str]]) -> str:
    prompt = f"""
User query:
{user_query}

Previous failed attempts:
{json.dumps(history, indent=2)}

Generate a corrected Spark SQL query.
Output only valid SQL.
"""
    response = LLM_CLIENT.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()