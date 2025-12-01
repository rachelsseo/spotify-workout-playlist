-- Core Tables (for documentation purposes)

-- playlists
CREATE TABLE IF NOT EXISTS playlists (
    playlist_id VARCHAR,
    snapshot_date DATE DEFAULT CURRENT_DATE,
    playlist_name VARCHAR,
    playlist_description VARCHAR,
    owner VARCHAR,
    owner_id VARCHAR,
    follower_count INTEGER,
    total_tracks INTEGER,
    playlist_url VARCHAR,
    category VARCHAR,
    search_query VARCHAR,
    data_source VARCHAR,  -- 'search', 'category', 'featured'
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, snapshot_date)
);

-- tracks (master table - deduplicated)
CREATE TABLE IF NOT EXISTS tracks (
    track_id VARCHAR PRIMARY KEY,
    track_name VARCHAR,
    track_name_clean VARCHAR,  -- cleaned ver 
    artist_id VARCHAR,
    artist_name VARCHAR,
    artist_name_clean VARCHAR,  -- cleaned ver
    artist_genres VARCHAR,
    album_id VARCHAR,
    album_name VARCHAR,
    album_type VARCHAR,
    release_date DATE,
    release_year INTEGER,
    duration_ms INTEGER,
    popularity INTEGER,
    explicit BOOLEAN,
    track_number INTEGER,
    disc_number INTEGER,
    is_local BOOLEAN,
    is_playable BOOLEAN,
    preview_url VARCHAR,
    isrc VARCHAR,  -- international standard recording code
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- playlist-track associations (temporal)
CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id VARCHAR,
    track_id VARCHAR,
    snapshot_date DATE DEFAULT CURRENT_DATE,
    playlist_name VARCHAR,
    position INTEGER,
    added_at TIMESTAMP,
    added_by_id VARCHAR,
    is_removed BOOLEAN DEFAULT FALSE,  -- if track was removed
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, track_id, snapshot_date)
);

-- artists (enriched data)
CREATE TABLE IF NOT EXISTS artists (
    artist_id VARCHAR PRIMARY KEY,
    artist_name VARCHAR,
    artist_name_clean VARCHAR,
    genres VARCHAR,
    popularity INTEGER,
    follower_count INTEGER,
    image_url VARCHAR,
    spotify_url VARCHAR,
    total_tracks_scraped INTEGER DEFAULT 0,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- albums (for album-based collection)
CREATE TABLE IF NOT EXISTS albums (
    album_id VARCHAR PRIMARY KEY,
    album_name VARCHAR,
    album_type VARCHAR,
    release_date DATE,
    release_year INTEGER,
    total_tracks INTEGER,
    label VARCHAR,
    artist_id VARCHAR,
    artist_name VARCHAR,
    popularity INTEGER,
    album_url VARCHAR,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracking Tables (Data Quality & Lineage)

-- tracking where each track came from (data lineage)
CREATE TABLE IF NOT EXISTS track_sources (
    track_id VARCHAR,
    source_type VARCHAR, 
    source_id VARCHAR,    
    source_name VARCHAR,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (track_id, source_type, source_id)
);

-- track data quality issues
CREATE SEQUENCE IF NOT EXISTS data_quality_issues_seq START 1;

CREATE TABLE IF NOT EXISTS data_quality_issues (
    issue_id INTEGER PRIMARY KEY DEFAULT nextval('data_quality_issues_seq'),
    record_type VARCHAR,  -- 'track', 'playlist', 'artist'
    record_id VARCHAR,
    issue_type VARCHAR,   -- 'missing_field', 'invalid_format', 'duplicate', etc.
    issue_description VARCHAR,
    severity VARCHAR,     -- 'low', 'medium', 'high'
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API call tracking (for monitoring rate limits)
CREATE SEQUENCE IF NOT EXISTS api_call_log_seq START 1;

CREATE TABLE IF NOT EXISTS api_call_log (
    call_id INTEGER PRIMARY KEY DEFAULT nextval('api_call_log_seq'),
    endpoint VARCHAR,
    method VARCHAR,
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message VARCHAR,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- tracking popularity over time (temporal analysis)
CREATE TABLE IF NOT EXISTS track_popularity_history (
    track_id VARCHAR,
    snapshot_date DATE,
    popularity INTEGER,
    playlist_count INTEGER,  -- how many playlists it appears in
    PRIMARY KEY (track_id, snapshot_date)
);

-- Performance Indexes

-- playlist indexes
CREATE INDEX IF NOT EXISTS idx_playlist_category ON playlists(category);
CREATE INDEX IF NOT EXISTS idx_playlist_snapshot ON playlists(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_playlist_followers ON playlists(follower_count DESC);

-- track indexes
CREATE INDEX IF NOT EXISTS idx_track_artist ON tracks(artist_name);
CREATE INDEX IF NOT EXISTS idx_track_popularity ON tracks(popularity DESC);
CREATE INDEX IF NOT EXISTS idx_track_release_year ON tracks(release_year);
CREATE INDEX IF NOT EXISTS idx_track_duration ON tracks(duration_ms);
CREATE INDEX IF NOT EXISTS idx_track_explicit ON tracks(explicit);
CREATE INDEX IF NOT EXISTS idx_track_name_clean ON tracks(track_name_clean);

-- artist indexes
CREATE INDEX IF NOT EXISTS idx_artist_popularity ON artists(popularity DESC);
CREATE INDEX IF NOT EXISTS idx_artist_followers ON artists(follower_count DESC);
CREATE INDEX IF NOT EXISTS idx_artist_name_clean ON artists(artist_name_clean);

-- playlist-track indexes
CREATE INDEX IF NOT EXISTS idx_pt_playlist ON playlist_tracks(playlist_id);
CREATE INDEX IF NOT EXISTS idx_pt_track ON playlist_tracks(track_id);
CREATE INDEX IF NOT EXISTS idx_pt_snapshot ON playlist_tracks(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_pt_position ON playlist_tracks(position);

-- source tracking indexes
CREATE INDEX IF NOT EXISTS idx_sources_track ON track_sources(track_id);
CREATE INDEX IF NOT EXISTS idx_sources_type ON track_sources(source_type);

-- temporal indexes
CREATE INDEX IF NOT EXISTS idx_popularity_history_track ON track_popularity_history(track_id);
CREATE INDEX IF NOT EXISTS idx_popularity_history_date ON track_popularity_history(snapshot_date);


-- Views for Analytics

-- track statistics (all together)
CREATE TABLE IF NOT EXISTS track_stats AS
SELECT 
    t.track_id,
    t.track_name,
    t.artist_name,
    t.popularity,
    COUNT(DISTINCT pt.playlist_id) as playlist_appearances,
    COUNT(DISTINCT ts.source_type) as source_diversity,
    MIN(t.first_seen_at) as first_discovered,
    MAX(pt.snapshot_date) as last_seen_in_playlist
FROM tracks t
LEFT JOIN playlist_tracks pt ON t.track_id = pt.track_id
LEFT JOIN track_sources ts ON t.track_id = ts.track_id
GROUP BY t.track_id, t.track_name, t.artist_name, t.popularity;

-- category statistics
CREATE TABLE IF NOT EXISTS category_stats AS
SELECT 
    p.category,
    COUNT(DISTINCT p.playlist_id) as playlist_count,
    COUNT(DISTINCT pt.track_id) as unique_tracks,
    AVG(t.duration_ms) as avg_duration,
    AVG(t.popularity) as avg_popularity
FROM playlists p
LEFT JOIN playlist_tracks pt ON p.playlist_id = pt.playlist_id
LEFT JOIN tracks t ON pt.track_id = t.track_id
GROUP BY p.category;