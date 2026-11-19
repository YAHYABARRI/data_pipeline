from __future__ import annotations

import csv
import hashlib
import shutil
from pathlib import Path
from typing import Any, Iterator

DATASET_HANDLE = "datascikhan/e-commerce-delivery-and-shipping-data-2026"
CSV_NAME = "E-commerce_Delivery_Shipping_Data_2026.csv"
REQUIRED_COLUMNS = (
    "order_id", "order_date", "customer_id", "customer_segment", "customer_city",
    "customer_country", "warehouse_id", "warehouse_city", "product_category",
    "product_weight_kg", "order_value_usd", "shipping_method", "carrier", "distance_km",
    "promised_delivery_days", "actual_delivery_days", "delivery_status", "late_delivery",
    "delivery_delay_days", "shipping_cost_usd", "package_size", "payment_method",
    "order_priority", "weather_condition", "customer_rating", "return_requested",
    "return_reason", "delivery_attempts", "warehouse_processing_hours", "tracking_status",
)
RAW_COLUMNS = (*REQUIRED_COLUMNS, "source_sha256", "source_row_number")
RAW_INSERT_SQL = f"""
    INSERT INTO ecommerce_orders_raw ({', '.join(RAW_COLUMNS)})
    VALUES ({', '.join(['%s'] * len(RAW_COLUMNS))})
    ON CONFLICT DO NOTHING
"""


def download_dataset(destination: str | Path) -> Path:
    """Download the public Kaggle dataset and copy its CSV to the project."""
    import kagglehub

    destination = Path(destination)
    cache_dir = Path(kagglehub.dataset_download(DATASET_HANDLE))
    source = next(cache_dir.rglob(CSV_NAME))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def source_metadata(csv_path: str | Path) -> dict[str, Any]:
    path = Path(csv_path)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "source_name": path.name,
        "source_path": str(path.resolve()),
        "source_sha256": digest.hexdigest(),
        "source_size_bytes": path.stat().st_size,
    }


def inspect_source(csv_path: str | Path) -> dict[str, Any]:
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        columns = next(reader, None) or []
        has_data = next(reader, None) is not None
    missing = sorted(set(REQUIRED_COLUMNS) - set(columns))
    return {
        "path": str(path), "columns": columns, "missing_columns": missing,
        "extra_columns": sorted(set(columns) - set(REQUIRED_COLUMNS)), "has_data": has_data,
    }


def iter_batches(csv_path: str | Path, chunk_size: int = 10_000) -> Iterator[list[tuple[Any, ...]]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        batch: list[tuple[Any, ...]] = []
        for row_number, row in enumerate(reader, start=2):
            values = tuple(row[column].strip() or None for column in REQUIRED_COLUMNS)
            batch.append((*values, row_number))
            if len(batch) == chunk_size:
                yield batch
                batch = []
        if batch:
            yield batch


def ingest_csv(conn: Any, csv_path: str | Path, chunk_size: int = 10_000) -> dict[str, Any]:
    meta = source_metadata(csv_path)
    missing = inspect_source(csv_path)["missing_columns"]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    with conn.cursor() as cur:
        cur.execute(
            "SELECT status, rows_seen FROM ecommerce_ingestion_runs WHERE source_sha256=%s",
            (meta["source_sha256"],),
        )
        previous = cur.fetchone()
        if previous and previous[0] == "succeeded":
            return meta | {"rows_seen": previous[1], "rows_inserted": 0, "already_loaded": True}
        cur.execute(
            """
            INSERT INTO ecommerce_ingestion_runs
              (source_name, source_path, source_sha256, source_size_bytes, status)
            VALUES (%s, %s, %s, %s, 'running')
            ON CONFLICT (source_sha256) DO UPDATE SET
              status='running', completed_at=NULL, started_at=NOW()
            """,
            (meta["source_name"], meta["source_path"], meta["source_sha256"], meta["source_size_bytes"]),
        )

    rows_seen = rows_inserted = 0
    for batch in iter_batches(csv_path, chunk_size):
        rows_seen += len(batch)
        values = [(*row[:-1], meta["source_sha256"], row[-1]) for row in batch]
        with conn.cursor() as cur:
            cur.executemany(RAW_INSERT_SQL, values, returning=False)
            rows_inserted += max(cur.rowcount, 0)

    with conn.cursor() as cur:
        cur.execute(
            """UPDATE ecommerce_ingestion_runs SET status='succeeded', rows_seen=%s,
               rows_inserted=%s, completed_at=NOW() WHERE source_sha256=%s""",
            (rows_seen, rows_inserted, meta["source_sha256"]),
        )
    return meta | {"rows_seen": rows_seen, "rows_inserted": rows_inserted, "already_loaded": False}

