-- Migration: Create earth health metrics tables
-- Replaces hardcoded frontend mock data with real, sourced, historical readings.

-- Cited data sources (one row per publisher/dataset)
CREATE TABLE alter_earth.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    organization VARCHAR(200) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    description TEXT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Metric definitions (static metadata - the card content)
CREATE TABLE alter_earth.earth_metrics (
    id VARCHAR(100) PRIMARY KEY,  -- slug, e.g. 'co2-level' (matches existing frontend ids)
    category VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    simplified_name VARCHAR(200) NOT NULL,
    icon VARCHAR(10) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    target_value DOUBLE PRECISION NOT NULL,
    target_description VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    action_info TEXT NOT NULL,

    -- Which direction is bad, used to derive trend/status from readings
    higher_is_worse BOOLEAN NOT NULL,
    -- Optional thresholds for status; NULL falls back to distance-from-target heuristic
    warning_threshold DOUBLE PRECISION NULL,
    critical_threshold DOUBLE PRECISION NULL,

    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Historical readings (the time series behind each metric's graph)
CREATE TABLE alter_earth.earth_metric_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id VARCHAR(100) NOT NULL REFERENCES alter_earth.earth_metrics(id) ON DELETE CASCADE,
    reading_date DATE NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    source_id UUID NOT NULL REFERENCES alter_earth.data_sources(id) ON DELETE RESTRICT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_metric_reading_date UNIQUE (metric_id, reading_date)
);

CREATE INDEX idx_earth_metric_readings_metric_date ON alter_earth.earth_metric_readings(metric_id, reading_date DESC);
CREATE INDEX idx_earth_metrics_active_order ON alter_earth.earth_metrics(is_active, display_order);

COMMENT ON TABLE alter_earth.earth_metrics IS 'Static metadata for each Earth Health Dashboard metric card';
COMMENT ON TABLE alter_earth.earth_metric_readings IS 'Historical time series readings behind each metric, one row per (metric, date)';
COMMENT ON TABLE alter_earth.data_sources IS 'Cited sources for earth_metric_readings, for transparency/reputability';
COMMENT ON COLUMN alter_earth.earth_metrics.higher_is_worse IS 'True if a rising value is bad (e.g. CO2), false if a rising value is good (e.g. renewable energy %)';
