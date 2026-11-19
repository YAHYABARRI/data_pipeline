import csv
from pathlib import Path

import pytest

from etl.ecommerce_extract import REQUIRED_COLUMNS, inspect_source, iter_batches, source_metadata


def valid_row() -> dict[str, str]:
    return {column: "value" for column in REQUIRED_COLUMNS} | {
        "order_id": "ORD-1", "order_date": "2026-01-01", "customer_id": "CUS-1",
        "product_weight_kg": "1.25", "order_value_usd": "100.00", "distance_km": "20",
        "promised_delivery_days": "3", "actual_delivery_days": "4", "late_delivery": "Yes",
        "delivery_delay_days": "1", "shipping_cost_usd": "5.00", "customer_rating": "4",
        "return_requested": "No", "return_reason": "None", "delivery_attempts": "1",
        "warehouse_processing_hours": "12.5",
    }


def write_csv(path: Path, rows: list[dict[str, str]], columns=REQUIRED_COLUMNS) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_inspect_and_batch_csv(tmp_path: Path):
    path = tmp_path / "orders.csv"
    write_csv(path, [valid_row(), valid_row() | {"order_id": "ORD-2"}])
    assert inspect_source(path)["has_data"] is True
    batches = list(iter_batches(path, chunk_size=1))
    assert len(batches) == 2
    assert batches[0][0][0] == "ORD-1"
    assert batches[0][0][-1] == 2


def test_empty_csv(tmp_path: Path):
    path = tmp_path / "empty.csv"
    write_csv(path, [])
    assert inspect_source(path)["has_data"] is False
    assert list(iter_batches(path)) == []


def test_missing_column_is_rejected(tmp_path: Path):
    path = tmp_path / "invalid.csv"
    columns = tuple(column for column in REQUIRED_COLUMNS if column != "order_id")
    write_csv(path, [], columns)
    with pytest.raises(ValueError, match="order_id"):
        list(iter_batches(path))


def test_hash_is_stable(tmp_path: Path):
    path = tmp_path / "orders.csv"
    write_csv(path, [valid_row()])
    assert source_metadata(path)["source_sha256"] == source_metadata(path)["source_sha256"]

