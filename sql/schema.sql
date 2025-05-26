-- Page Views Table
CREATE TABLE IF NOT EXISTS pageviews (
    event_id TEXT PRIMARY KEY,
    timestamp TIMESTAMP,
    user_id TEXT,
    session_id TEXT,
    page TEXT,
    device_type TEXT,
    load_time FLOAT
);

-- User Sessions Table
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    device_type TEXT,
    os TEXT,
    browser TEXT
);


-- User Activity Table
CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id TEXT,
    window_end_time TIMESTAMP,
    pageviews INTEGER,
    clicks INTEGER,
    scrolls INTEGER,
    form_submits INTEGER,
    video_plays INTEGER,
    pages_visited INTEGER
);


-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_pageviews_user_id ON pageviews(user_id);
CREATE INDEX IF NOT EXISTS idx_pageviews_timestamp ON pageviews(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);

-- Alerts table for storing alert history
CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved);

-- System metrics table for tracking performance
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id SERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp);
