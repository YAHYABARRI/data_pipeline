from pathlib import Path


def test_migration_is_additive_and_idempotent():
    sql = Path("migrations/001_lade_delivery.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists" in sql
    assert "drop table" not in sql
    assert "lade_ingestion_runs" in sql
    assert "lade_delivery_events" in sql
    assert "lade_daily_city_stats" in sql

