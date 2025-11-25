-- FrameSync SQLite Database Schema
-- Created: 2025-11-22
-- Purpose: Migrate from JSON files to SQLite for better performance and reliability

-- Users table: Track IP-based users (simple identification without authentication)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Devices table: Photo frame displays that fetch images
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,  -- e.g., "epaper-display-001"
    name TEXT NOT NULL,               -- e.g., "E-Paper Display"
    device_type TEXT NOT NULL,        -- e.g., "display"
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata_json TEXT DEFAULT '{}',  -- JSON blob for device-specific metadata
    CONSTRAINT valid_device_type CHECK (device_type IN ('display', 'kiosk', 'frame', 'other'))
);

-- Images table: Uploaded photos
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    uploader_ip TEXT NOT NULL,
    upload_time TEXT NOT NULL DEFAULT (datetime('now')),
    file_size INTEGER,                -- Size in bytes
    mime_type TEXT,                   -- e.g., "image/jpeg"
    width INTEGER,                    -- Image width in pixels
    height INTEGER,                   -- Image height in pixels
    -- EXIF metadata fields
    date_taken TEXT,                  -- Date/time photo was taken (from EXIF)
    camera_make TEXT,                 -- Camera manufacturer
    camera_model TEXT,                -- Camera model
    gps_latitude REAL,                -- GPS latitude
    gps_longitude REAL,               -- GPS longitude
    gps_altitude REAL,                -- GPS altitude in meters
    orientation INTEGER,              -- EXIF orientation (1-8)
    exif_json TEXT DEFAULT '{}',      -- Additional EXIF data as JSON blob
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (uploader_ip) REFERENCES users(ip_address) ON DELETE SET NULL
);

-- Image-Device assignments: Many-to-many relationship
-- An image can be assigned to multiple devices
-- A device can have multiple images assigned to it
CREATE TABLE IF NOT EXISTS image_device_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    device_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    UNIQUE(image_id, device_id)  -- Prevent duplicate assignments
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_uploader ON images(uploader_ip);
CREATE INDEX IF NOT EXISTS idx_images_upload_time ON images(upload_time);
CREATE INDEX IF NOT EXISTS idx_images_date_taken ON images(date_taken);
CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id);
CREATE INDEX IF NOT EXISTS idx_device_assignments_image ON image_device_assignments(image_id);
CREATE INDEX IF NOT EXISTS idx_device_assignments_device ON image_device_assignments(device_id);

-- Trigger to update users.updated_at on modification
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger to update devices.last_seen_at when accessed
CREATE TRIGGER IF NOT EXISTS update_devices_last_seen
AFTER UPDATE ON devices
FOR EACH ROW
BEGIN
    UPDATE devices SET last_seen_at = datetime('now') WHERE id = NEW.id;
END;

-- Notifications table: Push notifications for remote devices
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    action TEXT DEFAULT 'display_image',
    image_filename TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

-- Index for efficient notification queries by device
CREATE INDEX IF NOT EXISTS idx_notifications_device ON notifications(device_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);
