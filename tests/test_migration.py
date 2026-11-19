from pathlib import Path


def test_migration_is_additive_and_idempotent():
    sql = Path("migrations/002_ecommerce_delivery.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists" in sql
    assert "drop table" not in sql
    assert "ecommerce_ingestion_runs" in sql
    assert "ecommerce_orders" in sql
    assert "ecommerce_daily_stats" in sql
