#!/usr/bin/env python3
"""
Backfill EXIF data for existing images
Run this once to extract EXIF from all existing images
"""

import os
import sys
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Add current directory to path so we can import database module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

def extract_exif_data(filepath):
    """Extract EXIF metadata from an image file using Pillow."""
    exif_data = {
        'date_taken': None,
        'camera_make': None,
        'camera_model': None,
        'gps_latitude': None,
        'gps_longitude': None,
        'gps_altitude': None,
        'orientation': None,
        'exif_json': '{}'
    }

    try:
        with Image.open(filepath) as img:
            exif = img.getexif()

            if not exif:
                return exif_data

            # Additional EXIF data to store as JSON
            additional_exif = {}

            # Try to get GPS IFD (Image File Directory) if available
            gps_ifd = exif.get_ifd(0x8825)  # 0x8825 = GPSInfo tag

            # Process EXIF tags
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)

                # Extract specific fields we care about
                if tag == 'DateTime' or tag == 'DateTimeOriginal':
                    # Convert EXIF datetime format to ISO format
                    # EXIF format: "2024:11:23 14:30:45"
                    # ISO format: "2024-11-23T14:30:45"
                    try:
                        exif_data['date_taken'] = value.replace(':', '-', 2).replace(' ', 'T')
                    except (AttributeError, ValueError):
                        pass

                elif tag == 'Make':
                    exif_data['camera_make'] = str(value).strip()

                elif tag == 'Model':
                    exif_data['camera_model'] = str(value).strip()

                elif tag == 'Orientation':
                    exif_data['orientation'] = int(value)

                # Store other interesting EXIF fields in JSON
                elif tag in ['ExposureTime', 'FNumber', 'ISO', 'FocalLength', 'Flash', 'WhiteBalance', 'LensModel']:
                    try:
                        additional_exif[tag] = str(value)
                    except:
                        pass

            # Parse GPS data from GPS IFD if available
            if gps_ifd:
                gps_info = {}
                for gps_tag_id, gps_value in gps_ifd.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value

                # Convert GPS coordinates to decimal degrees
                if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
                    lat = gps_info['GPSLatitude']
                    lat_ref = gps_info['GPSLatitudeRef']
                    if isinstance(lat, tuple) and len(lat) == 3:
                        # Convert from degrees, minutes, seconds to decimal
                        decimal_lat = float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600
                        if lat_ref == 'S':
                            decimal_lat = -decimal_lat
                        exif_data['gps_latitude'] = decimal_lat

                if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
                    lon = gps_info['GPSLongitude']
                    lon_ref = gps_info['GPSLongitudeRef']
                    if isinstance(lon, tuple) and len(lon) == 3:
                        decimal_lon = float(lon[0]) + float(lon[1])/60 + float(lon[2])/3600
                        if lon_ref == 'W':
                            decimal_lon = -decimal_lon
                        exif_data['gps_longitude'] = decimal_lon

                if 'GPSAltitude' in gps_info:
                    alt = gps_info['GPSAltitude']
                    if isinstance(alt, (int, float)):
                        exif_data['gps_altitude'] = float(alt)

            # Store additional EXIF as JSON
            if additional_exif:
                exif_data['exif_json'] = json.dumps(additional_exif)

    except Exception as e:
        print(f"  Warning: Could not extract EXIF data: {e}")

    return exif_data

def backfill_exif():
    """Backfill EXIF data for all existing images"""
    print("Starting EXIF backfill for existing images...")

    # Get all images from database
    images = db.get_all_images()

    total = len(images)
    updated = 0
    skipped = 0
    errors = 0

    for i, img in enumerate(images, 1):
        filename = img['filename']
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        print(f"[{i}/{total}] Processing {filename}...", end=' ')

        # Check if file exists
        if not os.path.exists(filepath):
            print("SKIP (file not found)")
            skipped += 1
            continue

        # Check if already has EXIF data
        if img.get('date_taken') or img.get('camera_make') or img.get('gps_latitude'):
            print("SKIP (already has EXIF)")
            skipped += 1
            continue

        # Extract EXIF
        try:
            exif_data = extract_exif_data(filepath)

            # Update database
            with db.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE images
                    SET date_taken = ?,
                        camera_make = ?,
                        camera_model = ?,
                        gps_latitude = ?,
                        gps_longitude = ?,
                        gps_altitude = ?,
                        orientation = ?,
                        exif_json = ?
                    WHERE filename = ?
                ''', (
                    exif_data['date_taken'],
                    exif_data['camera_make'],
                    exif_data['camera_model'],
                    exif_data['gps_latitude'],
                    exif_data['gps_longitude'],
                    exif_data['gps_altitude'],
                    exif_data['orientation'],
                    exif_data['exif_json'],
                    filename
                ))

            # Show what was found
            found = []
            if exif_data['date_taken']:
                found.append('date')
            if exif_data['camera_make'] or exif_data['camera_model']:
                found.append('camera')
            if exif_data['gps_latitude']:
                found.append('GPS')

            if found:
                print(f"OK (found: {', '.join(found)})")
            else:
                print("OK (no EXIF data)")

            updated += 1

        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    print("\n" + "="*60)
    print(f"EXIF backfill complete!")
    print(f"  Total images: {total}")
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print("="*60)

if __name__ == '__main__':
    backfill_exif()
