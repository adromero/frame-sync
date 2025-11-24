#!/usr/bin/env python3
"""
Migration script to add EXIF fields to existing database
Run this once to update the schema
"""

import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'framesync.db')

def migrate():
    """Add EXIF fields to images table"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(images)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add EXIF columns if they don't exist
        if 'date_taken' not in columns:
            print("Adding date_taken column...")
            cursor.execute("ALTER TABLE images ADD COLUMN date_taken TEXT")

        if 'camera_make' not in columns:
            print("Adding camera_make column...")
            cursor.execute("ALTER TABLE images ADD COLUMN camera_make TEXT")

        if 'camera_model' not in columns:
            print("Adding camera_model column...")
            cursor.execute("ALTER TABLE images ADD COLUMN camera_model TEXT")

        if 'gps_latitude' not in columns:
            print("Adding gps_latitude column...")
            cursor.execute("ALTER TABLE images ADD COLUMN gps_latitude REAL")

        if 'gps_longitude' not in columns:
            print("Adding gps_longitude column...")
            cursor.execute("ALTER TABLE images ADD COLUMN gps_longitude REAL")

        if 'gps_altitude' not in columns:
            print("Adding gps_altitude column...")
            cursor.execute("ALTER TABLE images ADD COLUMN gps_altitude REAL")

        if 'orientation' not in columns:
            print("Adding orientation column...")
            cursor.execute("ALTER TABLE images ADD COLUMN orientation INTEGER")

        if 'exif_json' not in columns:
            print("Adding exif_json column...")
            cursor.execute("ALTER TABLE images ADD COLUMN exif_json TEXT DEFAULT '{}'")

        # Create index for date_taken if it doesn't exist
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_date_taken ON images(date_taken)")

        conn.commit()
        print("✓ Migration completed successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        print(f"Database not found: {DB_FILE}")
        print("Please ensure the database exists before running migration.")
        exit(1)

    print(f"Migrating database: {DB_FILE}")
    migrate()
