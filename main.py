from __future__ import annotations

import os
from pathlib import Path

import psycopg

from etl.ecommerce_extract import CSV_NAME, download_dataset
from etl.ecommerce_pipeline import run_pipeline


def get_connection() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"), port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "delivery_db"), user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "root"),
    )


def main() -> None:
    csv_path = Path(os.getenv("ECOMMERCE_CSV_PATH", f"datasets/raw/{CSV_NAME}"))
    if not csv_path.exists():
        download_dataset(csv_path)
    with get_connection() as conn:
        result = run_pipeline(conn, csv_path)
    print(
        f"E-commerce pipeline completed: {result['raw_rows']} raw rows, "
        f"{result['valid_rows']} valid rows, {result['invalid_rows']} invalid rows."
    )


if __name__ == "__main__":
    main()
