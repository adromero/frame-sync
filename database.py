"""
FrameSync Database Module
SQLite database operations and connection management
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import threading

# Database configuration
DB_FILE = os.path.join(os.path.dirname(__file__), 'framesync.db')
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'db_schema.sql')

# Thread-local storage for database connections (simple connection pooling)
_thread_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Get a thread-local database connection.
    This provides simple connection pooling - each thread gets its own connection.
    """
    if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
        _thread_local.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        _thread_local.connection.row_factory = sqlite3.Row  # Enable column access by name
        # Enable foreign key constraints
        _thread_local.connection.execute('PRAGMA foreign_keys = ON')
    return _thread_local.connection


@contextmanager
def get_cursor():
    """Context manager for database operations with automatic commit/rollback."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


def init_database() -> None:
    """Initialize the database with the schema if it doesn't exist."""
    if not os.path.exists(SCHEMA_FILE):
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()

    with get_cursor() as cursor:
        cursor.executescript(schema_sql)

    print(f"Database initialized: {DB_FILE}")


# ============================================================================
# USER OPERATIONS
# ============================================================================

def get_user_by_ip(ip_address: str) -> Optional[Dict[str, Any]]:
    """Get user by IP address."""
    with get_cursor() as cursor:
        cursor.execute(
            'SELECT * FROM users WHERE ip_address = ?',
            (ip_address,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_or_update_user(ip_address: str, name: str) -> Dict[str, Any]:
    """Create a new user or update existing user's name."""
    with get_cursor() as cursor:
        cursor.execute('''
            INSERT INTO users (ip_address, name, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(ip_address)
            DO UPDATE SET name = excluded.name, updated_at = datetime('now')
        ''', (ip_address, name))

        # Fetch the created/updated user
        cursor.execute('SELECT * FROM users WHERE ip_address = ?', (ip_address,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users."""
    with get_cursor() as cursor:
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# DEVICE OPERATIONS
# ============================================================================

def get_device_by_id(device_id: str) -> Optional[Dict[str, Any]]:
    """Get device by device_id."""
    with get_cursor() as cursor:
        cursor.execute(
            'SELECT * FROM devices WHERE device_id = ?',
            (device_id,)
        )
        row = cursor.fetchone()
        if row:
            device = dict(row)
            # Parse metadata JSON
            device['metadata'] = json.loads(device.get('metadata_json', '{}'))
            del device['metadata_json']
            return device
        return None


def create_or_update_device(device_id: str, name: str, device_type: str,
                            metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new device or update existing device."""
    metadata = metadata or {}
    metadata_json = json.dumps(metadata)

    with get_cursor() as cursor:
        cursor.execute('''
            INSERT INTO devices (device_id, name, device_type, metadata_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(device_id)
            DO UPDATE SET
                name = excluded.name,
                device_type = excluded.device_type,
                metadata_json = excluded.metadata_json,
                last_seen_at = datetime('now')
        ''', (device_id, name, device_type, metadata_json))

        return get_device_by_id(device_id)


def update_device_last_seen(device_id: str) -> None:
    """Update the last_seen_at timestamp for a device."""
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE devices SET last_seen_at = datetime('now') WHERE device_id = ?",
            (device_id,)
        )


def get_all_devices() -> List[Dict[str, Any]]:
    """Get all devices."""
    with get_cursor() as cursor:
        cursor.execute('SELECT * FROM devices ORDER BY registered_at DESC')
        devices = []
        for row in cursor.fetchall():
            device = dict(row)
            device['metadata'] = json.loads(device.get('metadata_json', '{}'))
            del device['metadata_json']
            devices.append(device)
        return devices


def delete_device(device_id: str) -> bool:
    """Delete a device and all its image assignments."""
    with get_cursor() as cursor:
        cursor.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
        return cursor.rowcount > 0


# ============================================================================
# IMAGE OPERATIONS
# ============================================================================

def create_image(filename: str, uploader_ip: str, file_size: Optional[int] = None,
                mime_type: Optional[str] = None, width: Optional[int] = None,
                height: Optional[int] = None) -> Dict[str, Any]:
    """Create a new image record."""
    with get_cursor() as cursor:
        cursor.execute('''
            INSERT INTO images (filename, uploader_ip, file_size, mime_type, width, height)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, uploader_ip, file_size, mime_type, width, height))

        image_id = cursor.lastrowid
        cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_image_by_filename(filename: str) -> Optional[Dict[str, Any]]:
    """Get image by filename."""
    with get_cursor() as cursor:
        cursor.execute('SELECT * FROM images WHERE filename = ?', (filename,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_images(limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all images with optional pagination."""
    with get_cursor() as cursor:
        query = 'SELECT * FROM images ORDER BY upload_time DESC'
        params = []

        if limit is not None:
            query += ' LIMIT ? OFFSET ?'
            params = [limit, offset]

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_images_count() -> int:
    """Get total count of images."""
    with get_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) as count FROM images')
        return cursor.fetchone()['count']


def delete_image(filename: str) -> bool:
    """Delete an image and all its device assignments."""
    with get_cursor() as cursor:
        cursor.execute('DELETE FROM images WHERE filename = ?', (filename,))
        return cursor.rowcount > 0


# ============================================================================
# IMAGE-DEVICE ASSIGNMENT OPERATIONS
# ============================================================================

def assign_image_to_device(filename: str, device_id: str) -> bool:
    """Assign an image to a device."""
    with get_cursor() as cursor:
        # Get image id
        cursor.execute('SELECT id FROM images WHERE filename = ?', (filename,))
        image_row = cursor.fetchone()
        if not image_row:
            return False

        image_id = image_row['id']

        # Create assignment (or ignore if already exists)
        cursor.execute('''
            INSERT OR IGNORE INTO image_device_assignments (image_id, device_id)
            VALUES (?, ?)
        ''', (image_id, device_id))

        return cursor.rowcount > 0


def unassign_image_from_device(filename: str, device_id: str) -> bool:
    """Remove image assignment from a device."""
    with get_cursor() as cursor:
        cursor.execute('''
            DELETE FROM image_device_assignments
            WHERE image_id = (SELECT id FROM images WHERE filename = ?)
            AND device_id = ?
        ''', (filename, device_id))

        return cursor.rowcount > 0


def set_image_devices(filename: str, device_ids: List[str]) -> None:
    """Set the complete list of devices for an image (replaces existing assignments)."""
    with get_cursor() as cursor:
        # Get image id
        cursor.execute('SELECT id FROM images WHERE filename = ?', (filename,))
        image_row = cursor.fetchone()
        if not image_row:
            raise ValueError(f"Image not found: {filename}")

        image_id = image_row['id']

        # Delete existing assignments
        cursor.execute('DELETE FROM image_device_assignments WHERE image_id = ?', (image_id,))

        # Add new assignments
        for device_id in device_ids:
            cursor.execute('''
                INSERT INTO image_device_assignments (image_id, device_id)
                VALUES (?, ?)
            ''', (image_id, device_id))


def get_image_devices(filename: str) -> List[str]:
    """Get list of device IDs assigned to an image."""
    with get_cursor() as cursor:
        cursor.execute('''
            SELECT device_id FROM image_device_assignments
            WHERE image_id = (SELECT id FROM images WHERE filename = ?)
            ORDER BY assigned_at ASC
        ''', (filename,))

        return [row['device_id'] for row in cursor.fetchall()]


def get_device_images(device_id: str) -> List[Dict[str, Any]]:
    """Get all images assigned to a specific device."""
    with get_cursor() as cursor:
        cursor.execute('''
            SELECT i.* FROM images i
            JOIN image_device_assignments ida ON i.id = ida.image_id
            WHERE ida.device_id = ?
            ORDER BY i.upload_time DESC
        ''', (device_id,))

        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def close_all_connections():
    """Close all thread-local database connections. Call on shutdown."""
    if hasattr(_thread_local, 'connection') and _thread_local.connection:
        _thread_local.connection.close()
        _thread_local.connection = None


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    with get_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM devices')
        devices_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM images')
        images_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM image_device_assignments')
        assignments_count = cursor.fetchone()['count']

        # Get database file size
        db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0

        return {
            'users': users_count,
            'devices': devices_count,
            'images': images_count,
            'assignments': assignments_count,
            'db_size_bytes': db_size,
            'db_file': DB_FILE
        }
