from pathlib import Path
import json
import glob
from ollama import Client
import jaydebeapi
from typing import List, Dict, Any
import yaml
from jinja2 import Template

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
def generate_sql(user_query: str, model: str, version: int) -> str:

    # Load YAML
    with open(f"/usr/app/ai/eval/version_control/{model}/eval_config_v{version}.yml", "r") as f:
        config = yaml.safe_load(f)

    # Render system prompt
    system_prompt = config["eval_config"]["prompt_templates"]["system"]
    
    # Render user prompt (per question)
    user_template = Template(config["eval_config"]["prompt_templates"]["user_template"])
    user_prompt = user_template.render(
        schema_block=config["eval_config"]["prompt_templates"]["schema_block"],
        semantic_block=config["eval_config"]["prompt_templates"]["semantic_block"],
        question=user_query
    )

    response = LLM_CLIENT.chat(
        model=config["eval_config"]["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_ctx": config["eval_config"]["window_size"],
            "temperature": config["eval_config"]["sampling"]["temperature"],
            "top_p": config["eval_config"]["sampling"]["top_p"]
            # "num_predict": config["eval_config"]["sampling"]["max_tokens"]
        }
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