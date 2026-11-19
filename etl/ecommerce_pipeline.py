from __future__ import annotations

from pathlib import Path
from typing import Any

from etl.ecommerce_extract import ingest_csv
from etl.ecommerce_transform import quality_report, refresh_daily_stats, transform_source


def run_pipeline(conn: Any, csv_path: str | Path, chunk_size: int = 10_000) -> dict[str, Any]:
    try:
        extracted = ingest_csv(conn, csv_path, chunk_size)
        transformed = transform_source(conn, extracted["source_sha256"])
        quality = quality_report(conn, extracted["source_sha256"])
        result = extracted | transformed | quality | {"aggregate_rows": refresh_daily_stats(conn)}
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise

