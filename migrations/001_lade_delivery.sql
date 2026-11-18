-- Additive LaDe migration. Existing learning tables and data are untouched.
CREATE TABLE IF NOT EXISTS lade_ingestion_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    source_size_bytes BIGINT NOT NULL CHECK (source_size_bytes >= 0),
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    rows_seen INTEGER NOT NULL DEFAULT 0 CHECK (rows_seen >= 0),
    rows_inserted INTEGER NOT NULL DEFAULT 0 CHECK (rows_inserted >= 0),
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE (source_sha256)
);

CREATE TABLE IF NOT EXISTS lade_delivery_raw (
    order_id TEXT PRIMARY KEY,
    from_dipan_id TEXT,
    from_city_name TEXT,
    delivery_user_id TEXT,
    poi_lng TEXT,
    poi_lat TEXT,
    aoi_id TEXT,
    typecode TEXT,
    receipt_time TEXT,
    receipt_lng TEXT,
    receipt_lat TEXT,
    sign_time TEXT,
    sign_lng TEXT,
    sign_lat TEXT,
    ds TEXT,
    source_sha256 CHAR(64) NOT NULL REFERENCES lade_ingestion_runs(source_sha256),
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 1),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_sha256, source_row_number)
);

CREATE TABLE IF NOT EXISTS lade_couriers (
    delivery_user_id TEXT PRIMARY KEY,
    first_seen_ds CHAR(4) NOT NULL CHECK (first_seen_ds ~ '^[0-1][0-9][0-3][0-9]$'),
    last_seen_ds CHAR(4) NOT NULL CHECK (last_seen_ds ~ '^[0-1][0-9][0-3][0-9]$'),
    city_count INTEGER NOT NULL CHECK (city_count > 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lade_delivery_events (
    order_id TEXT PRIMARY KEY REFERENCES lade_delivery_raw(order_id),
    region_id TEXT NOT NULL,
    city_name TEXT NOT NULL,
    delivery_user_id TEXT NOT NULL REFERENCES lade_couriers(delivery_user_id),
    poi_x DOUBLE PRECISION NOT NULL,
    poi_y DOUBLE PRECISION NOT NULL,
    aoi_id TEXT NOT NULL,
    typecode TEXT,
    receipt_month_day CHAR(5) NOT NULL CHECK (receipt_month_day ~ '^[0-1][0-9]-[0-3][0-9]$'),
    receipt_local_time TIME NOT NULL,
    receipt_x DOUBLE PRECISION NOT NULL,
    receipt_y DOUBLE PRECISION NOT NULL,
    sign_month_day CHAR(5) NOT NULL CHECK (sign_month_day ~ '^[0-1][0-9]-[0-3][0-9]$'),
    sign_local_time TIME NOT NULL,
    sign_x DOUBLE PRECISION,
    sign_y DOUBLE PRECISION,
    ds CHAR(4) NOT NULL CHECK (ds ~ '^[0-1][0-9][0-3][0-9]$'),
    source_sha256 CHAR(64) NOT NULL,
    transformed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK ((sign_x IS NULL) = (sign_y IS NULL))
);

CREATE TABLE IF NOT EXISTS lade_daily_city_stats (
    ds CHAR(4) NOT NULL,
    city_name TEXT NOT NULL,
    delivery_count INTEGER NOT NULL CHECK (delivery_count >= 0),
    courier_count INTEGER NOT NULL CHECK (courier_count >= 0),
    region_count INTEGER NOT NULL CHECK (region_count >= 0),
    aoi_count INTEGER NOT NULL CHECK (aoi_count >= 0),
    missing_typecode_count INTEGER NOT NULL CHECK (missing_typecode_count >= 0),
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (ds, city_name)
);

CREATE INDEX IF NOT EXISTS idx_lade_raw_source ON lade_delivery_raw (source_sha256);
CREATE INDEX IF NOT EXISTS idx_lade_events_ds_city ON lade_delivery_events (ds, city_name);
CREATE INDEX IF NOT EXISTS idx_lade_events_courier_ds ON lade_delivery_events (delivery_user_id, ds);
CREATE INDEX IF NOT EXISTS idx_lade_events_region ON lade_delivery_events (region_id);
CREATE INDEX IF NOT EXISTS idx_lade_events_aoi ON lade_delivery_events (aoi_id);

