import os

import psycopg
from airflow.sdk import dag, task , PokeReturnValue

from etl.create_summary import load_summary
from etl.extract_orders import extract_orders
from etl.transform_orders import transform_orders


def get_connection():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


@dag(
    dag_id="delivery_pipeline",
    schedule=None,
    catchup=False,
    tags=["delivery", "etl"],
)
def delivery_pipeline():
    @task()
    def extract_task():
        with get_connection() as conn:
            return extract_orders(conn)

    @task()
    def transform_task(orders):
        return transform_orders(orders)

    @task()
    def load_task(summary):
        with get_connection() as conn:
            load_summary(conn, summary)

    orders = extract_task()
    summary = transform_task(orders)
    load_task(summary)
   


delivery_pipeline()
