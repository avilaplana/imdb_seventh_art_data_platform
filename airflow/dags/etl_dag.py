from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable
from airflow.exceptions import AirflowSkipException
from airflow.utils.trigger_rule import TriggerRule
from docker.types import Mount
from spark_utils import build_spark_submit
from datetime import datetime, timedelta
import sys
import os

# Add extract src dir to path
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

##################################################
# FEATURE FLAG
##################################################

GLOBAL_EXTRACT_FLAG = "ENABLE_EXTRACT_STAGE"

##################################################
# FEATURE FLAG HELPER
##################################################

def skip_if_disabled(flag_name: str):
    enabled = Variable.get(flag_name, "true").lower() == "true"
    if not enabled:
        raise AirflowSkipException(f"{flag_name} disabled")

##################################################
# TASK CALLABLE
##################################################

def run_extract(script_name: str):
    # One global switch for ALL extract tasks
    skip_if_disabled(GLOBAL_EXTRACT_FLAG)

    module = __import__(script_name)
    module.main()

##################################################
# DAG
##################################################

with DAG(
    "daily_prod_etl_medallion",
    default_args=default_args,
    description="Extract to S3 -> Load to Iceberg (parallel Spark jobs)",
    schedule_interval=None,
    start_date=datetime(2025, 10, 1),
    catchup=False,
) as dag:

    ##################################################
    # Step 1: Extract all IMDB raw files to S3/MinIO #
    ##################################################
    EXTRACT_SCRIPT_DIR = "/opt/airflow/extract/src/"
    extract_raw_scripts = [
        "extract_name_basics_to_s3",
        "extract_title_principals_to_s3",
        "extract_title_akas_to_s3",
        "extract_title_basics_to_s3",
        "extract_title_crew_to_s3",
        "extract_title_episode_to_s3",
        "extract_title_ratings_to_s3"
        ]

    extract_tasks = []
    sys.path.append(EXTRACT_SCRIPT_DIR)

    for script in extract_raw_scripts:
        extract_task = PythonOperator(
            task_id=f"{script}",
            python_callable=run_extract,
            op_kwargs={"script_name": script},
        )
        extract_tasks.append(extract_task)

    ########################################################################
    # Step 2: Load each raw file from S3/MinIO to Iceberg using Spark jobs #
    ########################################################################
    SPARK_JOBS_DIR = "/opt/airflow/load/src/"
    load_bronze_jobs = [
        "create_tables",
        "load_to_iceberg_name_basics",
        "load_to_iceberg_title_akas",
        "load_to_iceberg_title_basics",
        "load_to_iceberg_title_crew",
        "load_to_iceberg_title_episode",
        "load_to_iceberg_title_principals",
        "load_to_iceberg_title_ratings"
        ]
    spark_bronze_tasks = []

    for job in load_bronze_jobs:
        spark_task_id = f"load_SPARK_bronze_{job}"
        spark_task = BashOperator(
            retries=0,          # fail fast on Spark job
            task_id=spark_task_id,
            bash_command=build_spark_submit(f"{SPARK_JOBS_DIR}{job}.py")
        )
        spark_bronze_tasks.append(spark_task)

    ############################################
    # Step 3: Install DBT dependencies #
    ############################################
    projects_dir = os.environ["PROJECTS_DIR"]
    
    dbt_deps_command = """deps
    --project-dir /usr/app/dbt/silver
    """
    
    dbt_deps_task = DockerOperator(
        task_id="transform_DBT_deps",
        image="dbt-spark:f5bf2ec",
        command=dbt_deps_command,
        mounts=[
                Mount(
                    source=f"{projects_dir}/seventh_art_analytics/transform",
                    target="/usr/app/dbt",
                    type="bind",
                )
            ],
        network_mode="seventh_art_analytics_iceberg_net",
        docker_url="unix://var/run/docker.sock",
        auto_remove=True,
        tty=True,
        mount_tmp_dir=False,
    )

    ############################################
    # Step 4: Install DBT seed #
    ############################################
    projects_dir = os.environ["PROJECTS_DIR"]

    dbt_seed_command = """seed
    --project-dir /usr/app/dbt/silver
    """

    dbt_seed_task = DockerOperator(
        task_id="transform_DBT_seed",
        image="dbt-spark:f5bf2ec",
        command=dbt_seed_command,
        mounts=[
                Mount(
                    source=f"{projects_dir}/seventh_art_analytics/transform",
                    target="/usr/app/dbt",
                    type="bind",
                )
            ],
        network_mode="seventh_art_analytics_iceberg_net",
        docker_url="unix://var/run/docker.sock",
        auto_remove=True,
        tty=True,
        mount_tmp_dir=False,
    )


    ############################################
    # Step 5: Transform Medallion Silver layer #
    ############################################
    dbt_silver_run_command = """run 
    --profiles-dir /usr/app/dbt 
    --target local 
    --project-dir /usr/app/dbt/silver
    """
    
    dbt_silver_run_task = DockerOperator(
        task_id="transform_DBT_silver_layer",
        image="dbt-spark:f5bf2ec",
        command=dbt_silver_run_command,
        mounts=[
                Mount(
                    source=f"{projects_dir}/seventh_art_analytics/transform",
                    target="/usr/app/dbt",
                    type="bind",
                )
            ],
        network_mode="seventh_art_analytics_iceberg_net",
        docker_url="unix://var/run/docker.sock",
        auto_remove=True,
        tty=True,
        mount_tmp_dir=False,
    )

     ############################################
    # Step 6: Data Validation Silver layer #
    ############################################
    dbt_silver_validation_command = """test
    --profiles-dir /usr/app/dbt 
    --target local 
    --project-dir /usr/app/dbt/silver
    """
    
    dbt_silver_validation_task = DockerOperator(
        task_id="transform_DBT_validation_silver_layer",
        image="dbt-spark:f5bf2ec",
        command=dbt_silver_validation_command,
        mounts=[
                Mount(
                    source=f"{projects_dir}/seventh_art_analytics/transform",
                    target="/usr/app/dbt",
                    type="bind",
                )
            ],
        network_mode="seventh_art_analytics_iceberg_net",
        docker_url="unix://var/run/docker.sock",
        auto_remove=True,
        tty=True,
        mount_tmp_dir=False,
    )
   
    extract_tasks >> spark_bronze_tasks[0]

    spark_bronze_tasks[0].trigger_rule = TriggerRule.NONE_FAILED

    spark_bronze_tasks[0] >> spark_bronze_tasks[1:8] >> \
        dbt_deps_task >> \
        dbt_seed_task >> \
        dbt_silver_run_task >> \
        dbt_silver_validation_task