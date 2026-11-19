-- Additive migration: existing project and LaDe tables remain untouched.
CREATE TABLE IF NOT EXISTS ecommerce_ingestion_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL UNIQUE,
    source_size_bytes BIGINT NOT NULL CHECK (source_size_bytes >= 0),
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    rows_seen INTEGER NOT NULL DEFAULT 0 CHECK (rows_seen >= 0),
    rows_inserted INTEGER NOT NULL DEFAULT 0 CHECK (rows_inserted >= 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ecommerce_orders_raw (
    order_id TEXT PRIMARY KEY,
    order_date TEXT, customer_id TEXT, customer_segment TEXT, customer_city TEXT,
    customer_country TEXT, warehouse_id TEXT, warehouse_city TEXT, product_category TEXT,
    product_weight_kg TEXT, order_value_usd TEXT, shipping_method TEXT, carrier TEXT,
    distance_km TEXT, promised_delivery_days TEXT, actual_delivery_days TEXT,
    delivery_status TEXT, late_delivery TEXT, delivery_delay_days TEXT,
    shipping_cost_usd TEXT, package_size TEXT, payment_method TEXT, order_priority TEXT,
    weather_condition TEXT, customer_rating TEXT, return_requested TEXT, return_reason TEXT,
    delivery_attempts TEXT, warehouse_processing_hours TEXT, tracking_status TEXT,
    source_sha256 CHAR(64) NOT NULL REFERENCES ecommerce_ingestion_runs(source_sha256),
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 1),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_sha256, source_row_number)
);

CREATE TABLE IF NOT EXISTS ecommerce_orders (
    order_id TEXT PRIMARY KEY REFERENCES ecommerce_orders_raw(order_id),
    order_date DATE NOT NULL,
    customer_id TEXT NOT NULL,
    customer_segment TEXT NOT NULL,
    customer_city TEXT NOT NULL,
    customer_country TEXT NOT NULL,
    warehouse_id TEXT NOT NULL,
    warehouse_city TEXT NOT NULL,
    product_category TEXT NOT NULL,
    product_weight_kg NUMERIC(10,2) NOT NULL CHECK (product_weight_kg >= 0),
    order_value_usd NUMERIC(12,2) NOT NULL CHECK (order_value_usd >= 0),
    shipping_method TEXT NOT NULL,
    carrier TEXT NOT NULL,
    distance_km NUMERIC(12,2) NOT NULL CHECK (distance_km >= 0),
    promised_delivery_days INTEGER NOT NULL CHECK (promised_delivery_days >= 0),
    actual_delivery_days INTEGER NOT NULL CHECK (actual_delivery_days >= 0),
    delivery_status TEXT NOT NULL,
    late_delivery BOOLEAN NOT NULL,
    delivery_delay_days INTEGER NOT NULL,
    shipping_cost_usd NUMERIC(12,2) NOT NULL CHECK (shipping_cost_usd >= 0),
    package_size TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    order_priority TEXT NOT NULL,
    weather_condition TEXT NOT NULL,
    customer_rating SMALLINT NOT NULL CHECK (customer_rating BETWEEN 1 AND 5),
    return_requested BOOLEAN NOT NULL,
    return_reason TEXT,
    delivery_attempts SMALLINT NOT NULL CHECK (delivery_attempts > 0),
    warehouse_processing_hours NUMERIC(8,2) NOT NULL CHECK (warehouse_processing_hours >= 0),
    tracking_status TEXT NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    transformed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ecommerce_daily_stats (
    order_date DATE PRIMARY KEY,
    order_count INTEGER NOT NULL,
    delivered_count INTEGER NOT NULL,
    late_count INTEGER NOT NULL,
    returned_count INTEGER NOT NULL,
    late_rate NUMERIC(7,4) NOT NULL,
    average_delivery_days NUMERIC(10,2) NOT NULL,
    order_value_usd NUMERIC(16,2) NOT NULL,
    shipping_cost_usd NUMERIC(16,2) NOT NULL,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ecommerce_orders_date ON ecommerce_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_ecommerce_orders_carrier ON ecommerce_orders (carrier);
CREATE INDEX IF NOT EXISTS idx_ecommerce_orders_warehouse ON ecommerce_orders (warehouse_id);
CREATE INDEX IF NOT EXISTS idx_ecommerce_orders_country ON ecommerce_orders (customer_country);

