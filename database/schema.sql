-- AI Parking Space Finder - PostgreSQL schema (site-based, source-agnostic design)
-- Run against the database named in config.DATABASE_URL
--
-- Replaces the earlier per-bay schema. Detection is source-agnostic (any
-- camera/footage), so the only site-specific thing we store is the
-- registered site itself: a name, its video source, and where it is on
-- the map. Occupancy is logged as aggregate free/occupied counts per
-- snapshot, not per individual bay.

CREATE TABLE IF NOT EXISTS sites (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    video_source  VARCHAR(255) NOT NULL,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS occupancy_snapshots (
    id              SERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    free_count      INTEGER NOT NULL,
    occupied_count  INTEGER NOT NULL,
    event_time      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_occupancy_snapshots_site_time
    ON occupancy_snapshots (site_id, event_time);

CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    username       VARCHAR(100) UNIQUE NOT NULL,
    role            VARCHAR(100) UNIQUE NOT NULL DEFAULT 'user',
    password_hash  VARCHAR(255) NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);