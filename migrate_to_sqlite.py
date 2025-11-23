#!/usr/bin/env python3
"""
FrameSync JSON to SQLite Migration Script

Migrates data from metadata.json and devices.json to SQLite database.
Creates a backup before migration and validates data integrity after.
"""

import json
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, Any
import database as db


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found, using empty dict")
        return {}

    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}")
        sys.exit(1)


def create_backup(backup_dir: str) -> None:
    """Create backup of JSON files before migration."""
    os.makedirs(backup_dir, exist_ok=True)

    files_to_backup = ['metadata.json', 'devices.json']
    for filename in files_to_backup:
        if os.path.exists(filename):
            dest = os.path.join(backup_dir, filename)
            shutil.copy2(filename, dest)
            print(f"✓ Backed up {filename} to {dest}")


def migrate_users(metadata: Dict[str, Any]) -> int:
    """Migrate users from metadata.json to database."""
    users = metadata.get('users', {})
    count = 0

    print("\nMigrating users...")
    for ip_address, user_data in users.items():
        name = user_data.get('name', 'Unknown')
        db.create_or_update_user(ip_address, name)
        print(f"  ✓ User: {name} ({ip_address})")
        count += 1

    return count


def migrate_devices(devices_data: Dict[str, Any]) -> int:
    """Migrate devices from devices.json to database."""
    devices = devices_data.get('devices', {})
    count = 0

    print("\nMigrating devices...")
    for device_id, device_info in devices.items():
        name = device_info.get('name', 'Unknown Device')
        device_type = device_info.get('device_type', 'display')
        metadata = device_info.get('metadata', {})

        db.create_or_update_device(device_id, name, device_type, metadata)
        print(f"  ✓ Device: {name} ({device_id})")
        count += 1

    return count


def migrate_images(metadata: Dict[str, Any]) -> int:
    """Migrate images from metadata.json to database."""
    images = metadata.get('images', {})
    count = 0

    print("\nMigrating images...")
    for filename, image_data in images.items():
        uploader_ip = image_data.get('uploader_ip', 'unknown')
        upload_time = image_data.get('upload_time')
        allowed_devices = image_data.get('allowed_devices', [])

        # Ensure user exists (create if missing from metadata.json)
        existing_user = db.get_user_by_ip(uploader_ip)
        if not existing_user:
            # Create user with IP as name
            db.create_or_update_user(uploader_ip, uploader_ip)
            print(f"  → Created missing user: {uploader_ip}")

        # Create image record
        try:
            db.create_image(
                filename=filename,
                uploader_ip=uploader_ip,
                file_size=None,  # Not stored in old JSON format
                mime_type=None,  # Not stored in old JSON format
                width=None,      # Not stored in old JSON format
                height=None      # Not stored in old JSON format
            )

            # Assign to devices
            for device_id in allowed_devices:
                db.assign_image_to_device(filename, device_id)

            print(f"  ✓ Image: {filename} -> {len(allowed_devices)} device(s)")
            count += 1

        except Exception as e:
            print(f"  ✗ Error migrating {filename}: {e}")

    return count


def validate_migration(metadata: Dict[str, Any], devices_data: Dict[str, Any]) -> bool:
    """Validate that migration was successful."""
    print("\nValidating migration...")

    # Check user counts (may be more than metadata due to missing user records for some images)
    expected_min_users = len(metadata.get('users', {}))
    actual_users = len(db.get_all_users())
    if actual_users < expected_min_users:
        print(f"  ✗ User count too low: expected at least {expected_min_users}, got {actual_users}")
        return False
    print(f"  ✓ Users: {actual_users} (at least {expected_min_users} from metadata)")

    # Check device counts
    expected_devices = len(devices_data.get('devices', {}))
    actual_devices = len(db.get_all_devices())
    if expected_devices != actual_devices:
        print(f"  ✗ Device count mismatch: expected {expected_devices}, got {actual_devices}")
        return False
    print(f"  ✓ Devices: {actual_devices}/{expected_devices}")

    # Check image counts
    expected_images = len(metadata.get('images', {}))
    actual_images = db.get_images_count()
    if expected_images != actual_images:
        print(f"  ✗ Image count mismatch: expected {expected_images}, got {actual_images}")
        return False
    print(f"  ✓ Images: {actual_images}/{expected_images}")

    # Validate a few random image-device assignments
    images = metadata.get('images', {})
    sample_count = min(5, len(images))
    if sample_count > 0:
        import random
        sample_images = random.sample(list(images.items()), sample_count)

        for filename, image_data in sample_images:
            expected_devices = set(image_data.get('allowed_devices', []))
            actual_devices = set(db.get_image_devices(filename))

            if expected_devices != actual_devices:
                print(f"  ✗ Device assignment mismatch for {filename}")
                print(f"    Expected: {expected_devices}")
                print(f"    Got: {actual_devices}")
                return False

        print(f"  ✓ Device assignments verified (sampled {sample_count} images)")

    return True


def print_stats() -> None:
    """Print database statistics after migration."""
    stats = db.get_database_stats()
    print("\n" + "="*60)
    print("Database Statistics")
    print("="*60)
    print(f"Users:       {stats['users']}")
    print(f"Devices:     {stats['devices']}")
    print(f"Images:      {stats['images']}")
    print(f"Assignments: {stats['assignments']}")
    print(f"DB Size:     {stats['db_size_bytes']:,} bytes ({stats['db_size_bytes']/1024:.2f} KB)")
    print(f"DB File:     {stats['db_file']}")
    print("="*60)


def main():
    """Main migration workflow."""
    print("="*60)
    print("FrameSync JSON to SQLite Migration")
    print("="*60)

    # Create backup
    backup_dir = f"backups/migration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"\nStep 1: Creating backup in {backup_dir}")
    create_backup(backup_dir)

    # Load JSON data
    print("\nStep 2: Loading JSON data")
    metadata = load_json_file('metadata.json')
    devices_data = load_json_file('devices.json')
    print(f"  ✓ Loaded {len(metadata.get('users', {}))} users")
    print(f"  ✓ Loaded {len(devices_data.get('devices', {}))} devices")
    print(f"  ✓ Loaded {len(metadata.get('images', {}))} images")

    # Initialize database
    print("\nStep 3: Initializing database")
    if os.path.exists(db.DB_FILE):
        response = input(f"Database {db.DB_FILE} already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            sys.exit(0)
        os.remove(db.DB_FILE)
        print(f"  ✓ Removed existing database")

    db.init_database()
    print(f"  ✓ Database initialized")

    # Migrate data
    print("\nStep 4: Migrating data")
    users_count = migrate_users(metadata)
    devices_count = migrate_devices(devices_data)
    images_count = migrate_images(metadata)

    print(f"\nMigration Summary:")
    print(f"  Users:   {users_count}")
    print(f"  Devices: {devices_count}")
    print(f"  Images:  {images_count}")

    # Validate migration
    print("\nStep 5: Validating migration")
    if validate_migration(metadata, devices_data):
        print("\n✓ Migration validation PASSED")
        print_stats()

        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Test the application with the new SQLite backend")
        print("2. If everything works, you can remove metadata.json and devices.json")
        print(f"3. Keep the backup in {backup_dir} until you're confident")
        print("\nTo revert to JSON:")
        print(f"  cp {backup_dir}/*.json ./")
        print(f"  rm {db.DB_FILE}")
        print("="*60)
    else:
        print("\n✗ Migration validation FAILED")
        print("Please review the errors above and try again.")
        sys.exit(1)


if __name__ == '__main__':
    main()
