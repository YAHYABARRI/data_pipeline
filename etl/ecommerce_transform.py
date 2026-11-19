from __future__ import annotations

from typing import Any

NUMBER = r"^-?[0-9]+(\.[0-9]+)?$"
INTEGER = r"^-?[0-9]+$"
VALID_RAW_ROW = f"""
    order_id IS NOT NULL AND customer_id IS NOT NULL AND order_date ~ '^2026-[0-1][0-9]-[0-3][0-9]$'
    AND TO_CHAR(TO_DATE(order_date, 'YYYY-MM-DD'), 'YYYY-MM-DD') = order_date
    AND product_weight_kg ~ '{NUMBER}' AND order_value_usd ~ '{NUMBER}'
    AND distance_km ~ '{NUMBER}' AND shipping_cost_usd ~ '{NUMBER}'
    AND warehouse_processing_hours ~ '{NUMBER}'
    AND promised_delivery_days ~ '{INTEGER}' AND actual_delivery_days ~ '{INTEGER}'
    AND delivery_delay_days ~ '{INTEGER}' AND customer_rating ~ '^[1-5]$'
    AND delivery_attempts ~ '^[1-9][0-9]*$'
    AND late_delivery IN ('Yes', 'No') AND return_requested IN ('Yes', 'No')
"""


def transform_source(conn: Any, source_sha256: str) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM ecommerce_orders_raw WHERE source_sha256=%s AND NOT ({VALID_RAW_ROW})",
            (source_sha256,),
        )
        invalid_rows = cur.fetchone()[0]
        cur.execute(
            f"""
            INSERT INTO ecommerce_orders (
              order_id, order_date, customer_id, customer_segment, customer_city, customer_country,
              warehouse_id, warehouse_city, product_category, product_weight_kg, order_value_usd,
              shipping_method, carrier, distance_km, promised_delivery_days, actual_delivery_days,
              delivery_status, late_delivery, delivery_delay_days, shipping_cost_usd, package_size,
              payment_method, order_priority, weather_condition, customer_rating, return_requested,
              return_reason, delivery_attempts, warehouse_processing_hours, tracking_status, source_sha256
            )
            SELECT order_id, order_date::date, customer_id, customer_segment, customer_city,
              customer_country, warehouse_id, warehouse_city, product_category,
              product_weight_kg::numeric, order_value_usd::numeric, shipping_method, carrier,
              distance_km::numeric, promised_delivery_days::integer, actual_delivery_days::integer,
              delivery_status, late_delivery='Yes', delivery_delay_days::integer,
              shipping_cost_usd::numeric, package_size, payment_method, order_priority,
              weather_condition, customer_rating::smallint, return_requested='Yes',
              NULLIF(return_reason, 'None'), delivery_attempts::smallint,
              warehouse_processing_hours::numeric, tracking_status, source_sha256
            FROM ecommerce_orders_raw WHERE source_sha256=%s AND ({VALID_RAW_ROW})
            ON CONFLICT (order_id) DO UPDATE SET
              delivery_status=EXCLUDED.delivery_status,
              tracking_status=EXCLUDED.tracking_status,
              transformed_at=NOW()
            """,
            (source_sha256,),
        )
        transformed_rows = max(cur.rowcount, 0)
    return {"invalid_rows": invalid_rows, "transformed_rows": transformed_rows}


def quality_report(conn: Any, source_sha256: str) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.rows_seen,
              (SELECT COUNT(*) FROM ecommerce_orders_raw WHERE source_sha256=r.source_sha256),
              (SELECT COUNT(*) FROM ecommerce_orders WHERE source_sha256=r.source_sha256)
            FROM ecommerce_ingestion_runs r WHERE r.source_sha256=%s
            """,
            (source_sha256,),
        )
        expected, raw, valid = cur.fetchone()
    if raw != expected:
        raise ValueError(f"Raw row mismatch: expected {expected}, found {raw}")
    if valid == 0 and expected:
        raise ValueError("No valid rows available for loading")
    return {"expected_rows": expected, "raw_rows": raw, "valid_rows": valid, "invalid_rows": raw - valid}


def refresh_daily_stats(conn: Any) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ecommerce_daily_stats (
              order_date, order_count, delivered_count, late_count, returned_count, late_rate,
              average_delivery_days, order_value_usd, shipping_cost_usd
            )
            SELECT order_date, COUNT(*), COUNT(*) FILTER (WHERE delivery_status='Delivered'),
              COUNT(*) FILTER (WHERE late_delivery), COUNT(*) FILTER (WHERE return_requested),
              ROUND(AVG(late_delivery::integer), 4), ROUND(AVG(actual_delivery_days), 2),
              ROUND(SUM(order_value_usd), 2), ROUND(SUM(shipping_cost_usd), 2)
            FROM ecommerce_orders GROUP BY order_date
            ON CONFLICT (order_date) DO UPDATE SET
              order_count=EXCLUDED.order_count, delivered_count=EXCLUDED.delivered_count,
              late_count=EXCLUDED.late_count, returned_count=EXCLUDED.returned_count,
              late_rate=EXCLUDED.late_rate, average_delivery_days=EXCLUDED.average_delivery_days,
              order_value_usd=EXCLUDED.order_value_usd,
              shipping_cost_usd=EXCLUDED.shipping_cost_usd, refreshed_at=NOW()
            """
        )
        return max(cur.rowcount, 0)

