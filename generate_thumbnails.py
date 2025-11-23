#!/usr/bin/env python3
"""
Migration script to generate thumbnails for all existing images.
This is part of CP2-T1: Generate Image Thumbnails
"""
import os
import sys
from PIL import Image

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
THUMBNAILS_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbnails')
THUMBNAIL_SIZE = (200, 200)
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}

def generate_thumbnail(filename, source_path, thumb_path):
    """
    Generate a thumbnail for an image.
    Returns (success, error_message)
    """
    try:
        # Open image and create thumbnail
        with Image.open(source_path) as img:
            # Convert RGBA to RGB if necessary (for PNG with transparency)
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            elif img.mode not in ('RGB', 'L'):  # L is grayscale
                img = img.convert('RGB')

            # Create thumbnail maintaining aspect ratio
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Save thumbnail with optimization
            img.save(thumb_path, 'JPEG', quality=85, optimize=True)

        return True, None
    except Exception as e:
        error_msg = f"Failed to generate thumbnail: {str(e)}"
        return False, error_msg

def main():
    """Generate thumbnails for all existing images"""
    print("=" * 60)
    print("Thumbnail Generation Script")
    print("=" * 60)
    print()

    # Check if upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"ERROR: Upload folder not found: {UPLOAD_FOLDER}")
        sys.exit(1)

    # Create thumbnails directory if it doesn't exist
    os.makedirs(THUMBNAILS_FOLDER, exist_ok=True)
    print(f"Thumbnails folder: {THUMBNAILS_FOLDER}")
    print()

    # Get all image files
    image_files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, filename)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                image_files.append(filename)

    if not image_files:
        print("No images found to process.")
        return

    print(f"Found {len(image_files)} images to process")
    print()

    # Process each image
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []

    for i, filename in enumerate(image_files, 1):
        source_path = os.path.join(UPLOAD_FOLDER, filename)
        thumb_path = os.path.join(THUMBNAILS_FOLDER, filename)

        # Skip if thumbnail already exists
        if os.path.exists(thumb_path):
            print(f"[{i}/{len(image_files)}] SKIP: {filename} (thumbnail exists)")
            skip_count += 1
            continue

        # Generate thumbnail
        print(f"[{i}/{len(image_files)}] Generating: {filename}...", end=' ')
        success, error = generate_thumbnail(filename, source_path, thumb_path)

        if success:
            # Get file sizes
            original_size = os.path.getsize(source_path)
            thumb_size = os.path.getsize(thumb_path)
            reduction = (1 - thumb_size / original_size) * 100
            print(f"OK ({thumb_size:,} bytes, {reduction:.1f}% smaller)")
            success_count += 1
        else:
            print(f"FAILED")
            error_count += 1
            errors.append((filename, error))

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total images:      {len(image_files)}")
    print(f"Generated:         {success_count}")
    print(f"Skipped (exists):  {skip_count}")
    print(f"Errors:            {error_count}")
    print()

    if errors:
        print("Errors:")
        for filename, error in errors:
            print(f"  - {filename}: {error}")
        print()

    if success_count > 0:
        print(f"✓ Successfully generated {success_count} thumbnails!")
    else:
        print("No new thumbnails generated.")

if __name__ == '__main__':
    main()
