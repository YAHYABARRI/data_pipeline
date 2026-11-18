from __future__ import annotations

from typing import Any


def transform_source(conn: Any, source_sha256: str) -> dict[str, int]:
    """Validate and upsert one source without inventing a year or coordinate CRS."""
    valid_predicate = """
        order_id IS NOT NULL AND from_dipan_id IS NOT NULL AND from_city_name IS NOT NULL
        AND delivery_user_id IS NOT NULL AND aoi_id IS NOT NULL
        AND poi_lng ~ '^-?[0-9]+(\\.[0-9]+)?$' AND poi_lat ~ '^-?[0-9]+(\\.[0-9]+)?$'
        AND receipt_lng ~ '^-?[0-9]+(\\.[0-9]+)?$' AND receipt_lat ~ '^-?[0-9]+(\\.[0-9]+)?$'
        AND receipt_time ~ '^[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'
        AND sign_time ~ '^[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'
        AND ds ~ '^[0-1][0-9][0-3][0-9]$'
        AND (sign_lng IS NULL OR sign_lng ~ '^-?[0-9]+(\\.[0-9]+)?$')
        AND (sign_lat IS NULL OR sign_lat ~ '^-?[0-9]+(\\.[0-9]+)?$')
        AND (sign_lng IS NULL) = (sign_lat IS NULL)
    """
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM lade_delivery_raw WHERE source_sha256=%s AND NOT ({valid_predicate})", (source_sha256,))
        invalid_rows = cur.fetchone()[0]
        cur.execute(
            f"""
            INSERT INTO lade_couriers (delivery_user_id, first_seen_ds, last_seen_ds, city_count)
            SELECT delivery_user_id, MIN(ds), MAX(ds), COUNT(DISTINCT from_city_name)
            FROM lade_delivery_raw WHERE source_sha256=%s AND ({valid_predicate})
            GROUP BY delivery_user_id
            ON CONFLICT (delivery_user_id) DO UPDATE SET
              first_seen_ds=LEAST(lade_couriers.first_seen_ds, EXCLUDED.first_seen_ds),
              last_seen_ds=GREATEST(lade_couriers.last_seen_ds, EXCLUDED.last_seen_ds),
              city_count=GREATEST(lade_couriers.city_count, EXCLUDED.city_count), updated_at=NOW()
            """,
            (source_sha256,),
        )
        cur.execute(
            f"""
            INSERT INTO lade_delivery_events
              (order_id, region_id, city_name, delivery_user_id, poi_x, poi_y, aoi_id,
               typecode, receipt_month_day, receipt_local_time, receipt_x, receipt_y,
               sign_month_day, sign_local_time, sign_x, sign_y, ds, source_sha256)
            SELECT order_id, from_dipan_id, from_city_name, delivery_user_id,
              poi_lng::double precision, poi_lat::double precision, aoi_id, typecode,
              LEFT(receipt_time,5), RIGHT(receipt_time,8)::time,
              receipt_lng::double precision, receipt_lat::double precision,
              LEFT(sign_time,5), RIGHT(sign_time,8)::time,
              sign_lng::double precision, sign_lat::double precision, ds, source_sha256
            FROM lade_delivery_raw WHERE source_sha256=%s AND ({valid_predicate})
            ON CONFLICT (order_id) DO UPDATE SET
              typecode=EXCLUDED.typecode, transformed_at=NOW()
            """,
            (source_sha256,),
        )
        transformed_rows = max(cur.rowcount, 0)
    return {"invalid_rows": invalid_rows, "transformed_rows": transformed_rows}


def refresh_daily_stats(conn: Any) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO lade_daily_city_stats
              (ds, city_name, delivery_count, courier_count, region_count, aoi_count, missing_typecode_count)
            SELECT ds, city_name, COUNT(*), COUNT(DISTINCT delivery_user_id),
              COUNT(DISTINCT region_id), COUNT(DISTINCT aoi_id), COUNT(*) FILTER (WHERE typecode IS NULL)
            FROM lade_delivery_events GROUP BY ds, city_name
            ON CONFLICT (ds, city_name) DO UPDATE SET
              delivery_count=EXCLUDED.delivery_count, courier_count=EXCLUDED.courier_count,
              region_count=EXCLUDED.region_count, aoi_count=EXCLUDED.aoi_count,
              missing_typecode_count=EXCLUDED.missing_typecode_count, refreshed_at=NOW()
            """
        )
        return max(cur.rowcount, 0)


def quality_report(conn: Any, source_sha256: str) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT rows_seen FROM lade_ingestion_runs WHERE source_sha256=%s", (source_sha256,))
        expected = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM lade_delivery_raw WHERE source_sha256=%s", (source_sha256,))
        raw = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM lade_delivery_events WHERE source_sha256=%s", (source_sha256,))
        valid = cur.fetchone()[0]
    if raw != expected:
        raise ValueError(f"Raw row mismatch: expected {expected}, found {raw}")
    if valid == 0 and expected > 0:
        raise ValueError("No valid rows available for loading")
    return {"expected_rows": expected, "raw_rows": raw, "valid_rows": valid, "invalid_rows": raw - valid}

