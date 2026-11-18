import csv
from pathlib import Path

import pytest

from etl.lade_extract import REQUIRED_COLUMNS, inspect_source, iter_batches, source_metadata


def write_csv(path: Path, rows: list[dict[str, str]], columns=REQUIRED_COLUMNS) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def valid_row() -> dict[str, str]:
    return {
        "order_id": "order-1", "from_dipan_id": "region-1", "from_city_name": "杭州市",
        "delivery_user_id": "courier-1", "poi_lng": "10448472.1", "poi_lat": "-7587086.1",
        "aoi_id": "aoi-1", "typecode": "type-1", "receipt_time": "03-18 07:28:00",
        "receipt_lng": "10447914.9", "receipt_lat": "-7586259.4",
        "sign_time": "03-20 12:40:00", "sign_lng": "", "sign_lat": "", "ds": "0318",
    }


def test_inspect_and_batch_unicode_csv(tmp_path: Path):
    path = tmp_path / "source.csv"
    write_csv(path, [valid_row(), {**valid_row(), "order_id": "order-2"}])
    audit = inspect_source(path)
    assert audit["has_data"] is True
    assert audit["missing_columns"] == []
    batches = list(iter_batches(path, chunk_size=1))
    assert len(batches) == 2
    assert batches[0][0][2] == "杭州市"
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
    path = tmp_path / "source.csv"
    write_csv(path, [valid_row()])
    assert source_metadata(path)["source_sha256"] == source_metadata(path)["source_sha256"]

