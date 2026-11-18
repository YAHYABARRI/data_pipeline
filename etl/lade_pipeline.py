from __future__ import annotations

from pathlib import Path
from typing import Any

from etl.lade_extract import ingest_csv
from etl.lade_transform import quality_report, refresh_daily_stats, transform_source


def run_lade_pipeline(conn: Any, csv_path: str | Path, chunk_size: int = 10_000) -> dict[str, Any]:
    try:
        extracted = ingest_csv(conn, csv_path, chunk_size)
        transformed = transform_source(conn, extracted["source_sha256"])
        quality = quality_report(conn, extracted["source_sha256"])
        aggregate_rows = refresh_daily_stats(conn)
        conn.commit()
        return {**extracted, **transformed, **quality, "aggregate_rows": aggregate_rows}
    except Exception:
        conn.rollback()
        raise

