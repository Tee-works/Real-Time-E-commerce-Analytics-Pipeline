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

