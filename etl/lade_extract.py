from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any, Iterator

REQUIRED_COLUMNS = (
    "order_id", "from_dipan_id", "from_city_name", "delivery_user_id",
    "poi_lng", "poi_lat", "aoi_id", "typecode", "receipt_time",
    "receipt_lng", "receipt_lat", "sign_time", "sign_lng", "sign_lat", "ds",
)


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
        header = next(reader, None)
        first_row = next(reader, None)
    if header is None:
        return {"path": str(path), "columns": [], "has_data": False}
    missing = sorted(set(REQUIRED_COLUMNS) - set(header))
    extra = sorted(set(header) - set(REQUIRED_COLUMNS))
    return {
        "path": str(path), "columns": header, "missing_columns": missing,
        "extra_columns": extra, "has_data": first_row is not None,
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
            batch.append(tuple(row[column].strip() or None for column in REQUIRED_COLUMNS) + (row_number,))
            if len(batch) == chunk_size:
                yield batch
                batch = []
        if batch:
            yield batch


def ingest_csv(conn: Any, csv_path: str | Path, chunk_size: int = 10_000) -> dict[str, Any]:
    meta = source_metadata(csv_path)
    audit = inspect_source(csv_path)
    if audit["missing_columns"]:
        raise ValueError(f"Missing required columns: {', '.join(audit['missing_columns'])}")

    with conn.cursor() as cur:
        cur.execute("SELECT status, rows_seen, rows_inserted FROM lade_ingestion_runs WHERE source_sha256 = %s", (meta["source_sha256"],))
        previous = cur.fetchone()
        if previous and previous[0] == "succeeded":
            return {**meta, "rows_seen": previous[1], "rows_inserted": 0, "already_loaded": True}
        cur.execute(
            """
            INSERT INTO lade_ingestion_runs
                (source_name, source_path, source_sha256, source_size_bytes, status)
            VALUES (%s, %s, %s, %s, 'running')
            ON CONFLICT (source_sha256) DO UPDATE
            SET status='running', error_message=NULL, completed_at=NULL, started_at=NOW()
            """,
            (meta["source_name"], meta["source_path"], meta["source_sha256"], meta["source_size_bytes"]),
        )

    rows_seen = rows_inserted = 0
    columns = ", ".join(REQUIRED_COLUMNS) + ", source_sha256, source_row_number"
    placeholders = ", ".join(["%s"] * (len(REQUIRED_COLUMNS) + 2))
    sql = f"INSERT INTO lade_delivery_raw ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    for batch in iter_batches(csv_path, chunk_size):
        rows_seen += len(batch)
        values = [row[:-1] + (meta["source_sha256"], row[-1]) for row in batch]
        with conn.cursor() as cur:
            cur.executemany(sql, values, returning=False)
            rows_inserted += max(cur.rowcount, 0)

    with conn.cursor() as cur:
        cur.execute(
            """UPDATE lade_ingestion_runs SET status='succeeded', rows_seen=%s,
               rows_inserted=%s, completed_at=NOW() WHERE source_sha256=%s""",
            (rows_seen, rows_inserted, meta["source_sha256"]),
        )
    return {**meta, "rows_seen": rows_seen, "rows_inserted": rows_inserted, "already_loaded": False}

