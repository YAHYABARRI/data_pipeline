-- Optional rollback. Run explicitly only if the LaDe migration must be removed.
DROP TABLE IF EXISTS lade_daily_city_stats;
DROP TABLE IF EXISTS lade_delivery_events;
DROP TABLE IF EXISTS lade_couriers;
DROP TABLE IF EXISTS lade_delivery_raw;
DROP TABLE IF EXISTS lade_ingestion_runs;

