from __future__ import annotations

import os
from datetime import timedelta

import psycopg
from airflow.sdk import BaseHook, dag, task

from etl.ecommerce_extract import ingest_csv, inspect_source, source_metadata
from etl.ecommerce_transform import quality_report, refresh_daily_stats, transform_source

CSV_PATH = os.getenv(
    "ECOMMERCE_CSV_PATH",
    "/opt/airflow/datasets/raw/E-commerce_Delivery_Shipping_Data_2026.csv",
)


def get_connection():
    """Use the Airflow Connection, with environment variables as a local fallback."""
    try:
        connection = BaseHook.get_connection("delivery_postgres")
        return psycopg.connect(
            host=connection.host, port=connection.port or 5432,
            dbname=connection.schema, user=connection.login, password=connection.password,
        )
    except Exception:
        return psycopg.connect(
            host=os.environ["DB_HOST"], port=os.environ.get("DB_PORT", "5432"),
            dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )


@dag(
    dag_id="delivery_pipeline", schedule=None, catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["delivery", "ecommerce", "etl"],
)
def delivery_pipeline():
    @task
    def inspect_source_task() -> dict:
        return inspect_source(CSV_PATH) | source_metadata(CSV_PATH)

    @task.branch
    def check_data(source: dict) -> str:
        if source["missing_columns"]:
            raise ValueError(f"Missing columns: {source['missing_columns']}")
        return "extract_batches" if source["has_data"] else "skip_processing"

    @task
    def extract_batches(source: dict) -> dict:
        with get_connection() as conn:
            return ingest_csv(conn, source["path"])

    @task
    def transform_data(extracted: dict) -> dict:
        with get_connection() as conn:
            result = transform_source(conn, extracted["source_sha256"])
        return extracted | result

    @task
    def check_data_quality(transformed: dict) -> dict:
        with get_connection() as conn:
            result = quality_report(conn, transformed["source_sha256"])
        return transformed | result

    @task
    def load_data(validated: dict) -> dict:
        with get_connection() as conn:
            aggregate_rows = refresh_daily_stats(conn)
        return validated | {"aggregate_rows": aggregate_rows}

    @task
    def skip_processing() -> None:
        return None

    @task(trigger_rule="none_failed_min_one_success")
    def finish() -> None:
        return None

    source = inspect_source_task()
    branch = check_data(source)
    extracted = extract_batches(source)
    transformed = transform_data(extracted)
    validated = check_data_quality(transformed)
    loaded = load_data(validated)
    skipped = skip_processing()
    branch >> [extracted, skipped]
    [loaded, skipped] >> finish()


delivery_pipeline()
