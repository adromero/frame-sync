#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
import socket
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import random
from PIL import Image
import database as db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('framesync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
THUMBNAILS_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbnails')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
THUMBNAIL_SIZE = (200, 200)  # Thumbnail dimensions
STORAGE_QUOTA = 5 * 1024 * 1024 * 1024  # 5GB default storage quota
QUOTA_WARNING_THRESHOLD = 0.90  # Warn when 90% full

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Enable CORS for all routes
CORS(app)

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True  # Add rate limit headers to responses
)

# Global variable to track current image (temporary state, not persisted)
current_image_state = None

# Error response helpers
def error_response(message, code=None, status_code=400):
    """
    Create a standardized error response.

    Args:
        message: Human-readable error message
        code: Optional error code for programmatic handling
        status_code: HTTP status code (default 400)

    Returns:
        Flask response tuple (json, status_code)
    """
    response = {
        'success': False,
        'error': {
            'message': message
        }
    }
    if code:
        response['error']['code'] = code

    logger.warning(f"Error response ({status_code}): {message}")
    return jsonify(response), status_code

def success_response(data=None, message=None):
    """
    Create a standardized success response.

    Args:
        data: Response data (optional)
        message: Success message (optional)

    Returns:
        Flask response
    """
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message

    return jsonify(response)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(filepath):
    """
    Validate that a file is actually a valid image using Pillow.
    Returns (is_valid, error_message)
    """
    try:
        # Open and verify the image
        with Image.open(filepath) as img:
            # verify() checks the file header without loading the entire image
            img.verify()

        # Re-open to check it can be fully loaded
        # (verify() consumes the image object)
        with Image.open(filepath) as img:
            # Try to load the image data
            img.load()

        return True, None
    except (IOError, OSError, Image.UnidentifiedImageError) as e:
        error_msg = f"Invalid image file: {str(e)}"
        logger.warning(f"Image validation failed for {filepath}: {e}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error validating image: {str(e)}"
        logger.error(f"Unexpected error validating image {filepath}: {e}", exc_info=True)
        return False, error_msg

def generate_thumbnail(filename):
    """
    Generate a thumbnail for an uploaded image.
    Returns (success, error_message)
    """
    try:
        # Ensure thumbnails directory exists
        os.makedirs(THUMBNAILS_FOLDER, exist_ok=True)

        # Paths
        source_path = os.path.join(UPLOAD_FOLDER, filename)
        thumb_path = os.path.join(THUMBNAILS_FOLDER, filename)

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
    except (IOError, OSError) as e:
        error_msg = f"Failed to generate thumbnail: {str(e)}"
        logger.error(f"Thumbnail generation failed for {filename}: {e}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error generating thumbnail: {str(e)}"
        logger.error(f"Unexpected error generating thumbnail for {filename}: {e}", exc_info=True)
        return False, error_msg

def calculate_storage_usage():
    """
    Calculate current storage usage for uploads and thumbnails.
    Returns dict with usage statistics in bytes.
    """
    try:
        total_size = 0
        image_count = 0

        # Calculate uploads folder size
        if os.path.exists(UPLOAD_FOLDER):
            for root, dirs, files in os.walk(UPLOAD_FOLDER):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        # Don't count thumbnails directory in main uploads
                        if not filepath.startswith(THUMBNAILS_FOLDER):
                            file_size = os.path.getsize(filepath)
                            total_size += file_size
                            image_count += 1
                    except (OSError, IOError) as e:
                        logger.warning(f"Could not get size for {filepath}: {e}")

        # Calculate thumbnails folder size
        thumbnail_size = 0
        thumbnail_count = 0
        if os.path.exists(THUMBNAILS_FOLDER):
            for file in os.listdir(THUMBNAILS_FOLDER):
                filepath = os.path.join(THUMBNAILS_FOLDER, file)
                try:
                    if os.path.isfile(filepath):
                        file_size = os.path.getsize(filepath)
                        thumbnail_size += file_size
                        thumbnail_count += 1
                except (OSError, IOError) as e:
                    logger.warning(f"Could not get size for thumbnail {filepath}: {e}")

        total_with_thumbnails = total_size + thumbnail_size

        return {
            'total_bytes': total_with_thumbnails,
            'images_bytes': total_size,
            'thumbnails_bytes': thumbnail_size,
            'image_count': image_count,
            'thumbnail_count': thumbnail_count,
            'quota_bytes': STORAGE_QUOTA,
            'quota_used_percent': (total_with_thumbnails / STORAGE_QUOTA * 100) if STORAGE_QUOTA > 0 else 0,
            'quota_available_bytes': max(0, STORAGE_QUOTA - total_with_thumbnails)
        }
    except Exception as e:
        logger.error(f"Error calculating storage usage: {e}", exc_info=True)
        return {
            'total_bytes': 0,
            'images_bytes': 0,
            'thumbnails_bytes': 0,
            'image_count': 0,
            'thumbnail_count': 0,
            'quota_bytes': STORAGE_QUOTA,
            'quota_used_percent': 0,
            'quota_available_bytes': STORAGE_QUOTA
        }

def add_image_metadata(filename, uploader_ip, allowed_devices=None):
    """Add metadata for a newly uploaded image"""
    allowed_devices = allowed_devices if allowed_devices is not None else []

    # Get file info
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else None

    # Try to get image dimensions
    width, height = None, None
    try:
        with Image.open(filepath) as img:
            width, height = img.size
    except (IOError, OSError) as e:
        logger.warning(f"Could not read image dimensions for {filename}: {e}")

    # Detect MIME type
    mime_type = None
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                'gif': 'image/gif', 'bmp': 'image/bmp'}
    mime_type = mime_map.get(ext)

    # Ensure user exists (create if needed) to satisfy foreign key constraint
    db.create_or_update_user(uploader_ip, uploader_ip)

    # Create image record
    image = db.create_image(filename, uploader_ip, file_size, mime_type, width, height)

    # Set device assignments
    if allowed_devices:
        db.set_image_devices(filename, allowed_devices)

    return image

def remove_image_metadata(filename):
    """Remove metadata for a deleted image"""
    db.delete_image(filename)

def set_user_name(ip, name):
    """Set a display name for a user IP"""
    db.create_or_update_user(ip, name)

def get_user_name(ip):
    """Get the display name for a user IP, or return the IP if no name set"""
    user = db.get_user_by_ip(ip)
    return user['name'] if user else ip

def get_all_users():
    """Get list of all unique uploader IPs with their names"""
    users = db.get_all_users()
    return [{'ip': user['ip_address'], 'name': user['name']} for user in users]

def get_image_list(filter_user=None, page=None, limit=None, search=None, date_from=None, date_to=None, device_id=None):
    """Get list of uploaded images with metadata

    Args:
        filter_user: Optional IP address to filter images by uploader
        page: Optional page number (1-indexed) for pagination
        limit: Optional number of items per page
        search: Optional search query for filename (case-insensitive)
        date_from: Optional start date filter (YYYY-MM-DD format)
        date_to: Optional end date filter (YYYY-MM-DD format)
        device_id: Optional device ID to filter images assigned to specific device

    Returns:
        If pagination params provided: dict with {'images': [...], 'total': N, 'page': N, 'pages': N}
        Otherwise: list of images (for backward compatibility)
    """
    from datetime import datetime

    # Get all images from database
    all_images = db.get_all_images()

    # Parse date filters if provided
    date_from_dt = None
    date_to_dt = None
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
        except ValueError:
            logging.warning(f"Invalid date_from format: {date_from}")
    if date_to:
        try:
            # Set to end of day (23:59:59) to include entire end date
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            logging.warning(f"Invalid date_to format: {date_to}")

    # Build response with device assignments
    images = []
    for img in all_images:
        # Apply user filter if specified
        if filter_user and img['uploader_ip'] != filter_user:
            continue

        # Apply filename search filter if specified
        if search and search.lower() not in img['filename'].lower():
            continue

        # Apply date range filter if specified
        if date_from_dt or date_to_dt:
            try:
                img_date = datetime.fromisoformat(img['upload_time'])
                if date_from_dt and img_date < date_from_dt:
                    continue
                if date_to_dt and img_date > date_to_dt:
                    continue
            except (ValueError, TypeError):
                logging.warning(f"Invalid upload_time for image {img['filename']}: {img['upload_time']}")
                continue

        # Get device assignments
        allowed_devices = db.get_image_devices(img['filename'])

        # Apply device filter if specified
        if device_id and device_id not in allowed_devices:
            continue

        images.append({
            'filename': img['filename'],
            'size': img['file_size'] or 0,
            'uploaded': img['upload_time'],
            'uploader_ip': img['uploader_ip'],
            'uploader_name': get_user_name(img['uploader_ip']),
            'allowed_devices': allowed_devices
        })

    # If pagination params not provided, return simple list (backward compatibility)
    if page is None or limit is None:
        return images

    # Apply pagination
    total_images = len(images)
    total_pages = (total_images + limit - 1) // limit if limit > 0 else 1  # Ceiling division

    # Ensure page is within valid range
    page = max(1, min(page, total_pages if total_pages > 0 else 1))

    # Calculate slice indices
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_images = images[start_idx:end_idx]

    return {
        'images': paginated_images,
        'total': total_images,
        'page': page,
        'pages': total_pages,
        'limit': limit
    }

def get_current_image():
    """Get the currently displayed image"""
    global current_image_state
    return current_image_state

def set_current_image(filename):
    """Set the currently displayed image"""
    global current_image_state
    current_image_state = filename

# Device Management Functions

def register_device(device_id, name, device_type='display', metadata=None):
    """Register or update a device"""
    existing = db.get_device_by_id(device_id)
    is_new = existing is None

    db.create_or_update_device(device_id, name, device_type, metadata or {})
    return is_new

def update_device_last_seen(device_id):
    """Update the last seen timestamp for a device"""
    db.update_device_last_seen(device_id)

def get_device(device_id):
    """Get a specific device by ID"""
    device = db.get_device_by_id(device_id)
    if not device:
        return None

    # Convert database format to API format
    return {
        'name': device['name'],
        'device_type': device['device_type'],
        'registered': device['registered_at'],
        'last_seen': device['last_seen_at'],
        'metadata': device['metadata']
    }

def get_all_devices():
    """Get all registered devices"""
    devices = db.get_all_devices()

    # Convert to dict format expected by API (device_id as key)
    devices_dict = {}
    for device in devices:
        device_id = device['device_id']
        devices_dict[device_id] = {
            'name': device['name'],
            'device_type': device['device_type'],
            'registered': device['registered_at'],
            'last_seen': device['last_seen_at'],
            'metadata': device['metadata']
        }
    return devices_dict

def delete_device(device_id):
    """Remove a device from the registry"""
    return db.delete_device(device_id)

def update_image_devices(filename, allowed_devices):
    """Update the list of devices allowed to view an image"""
    try:
        db.set_image_devices(filename, allowed_devices)
        return True
    except ValueError:
        return False

def get_images_for_device(device_id):
    """Get all images that a specific device is allowed to view"""
    images = db.get_device_images(device_id)

    # Convert to expected format
    result = []
    for img in images:
        result.append({
            'filename': img['filename'],
            'size': img['file_size'] or 0,
            'uploaded': img['upload_time'],
            'uploader_ip': img['uploader_ip'],
            'uploader_name': get_user_name(img['uploader_ip'])
        })

    return result

@app.route('/')
def index():
    response = render_template('index.html')
    return response

@app.after_request
def add_no_cache_headers(response):
    """Add headers to prevent caching of HTML pages"""
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

@app.route('/api/images')
def list_images():
    """API endpoint to list all uploaded images with optional pagination and filtering"""
    filter_user = request.args.get('user')  # Optional filter by user IP
    page = request.args.get('page', type=int)  # Optional page number (1-indexed)
    limit = request.args.get('limit', type=int)  # Optional items per page
    search = request.args.get('search')  # Optional search query for filename
    date_from = request.args.get('date_from')  # Optional start date (YYYY-MM-DD)
    date_to = request.args.get('date_to')  # Optional end date (YYYY-MM-DD)
    device_id = request.args.get('device')  # Optional filter by device ID

    # Get image list (with or without pagination)
    result = get_image_list(
        filter_user=filter_user,
        page=page,
        limit=limit,
        search=search,
        date_from=date_from,
        date_to=date_to,
        device_id=device_id
    )
    current = get_current_image()

    # Handle both paginated and non-paginated responses
    if isinstance(result, dict):
        # Paginated response
        return jsonify({
            'images': result['images'],
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'limit': result['limit'],
            'current_image': current
        })
    else:
        # Non-paginated response (backward compatibility)
        return jsonify({'images': result, 'current_image': current})

@app.route('/api/users')
def list_users():
    """API endpoint to list all unique uploaders"""
    users = get_all_users()

    # Count images per user from database
    all_images = db.get_all_images()
    user_counts = {}
    for img in all_images:
        ip = img['uploader_ip']
        user_counts[ip] = user_counts.get(ip, 0) + 1

    users_with_counts = [{'ip': user['ip'], 'name': user['name'], 'image_count': user_counts.get(user['ip'], 0)} for user in users]
    return jsonify({'users': users_with_counts})

@app.route('/api/user/name', methods=['POST'])
@limiter.limit("60 per minute")
def set_user_name_endpoint():
    """API endpoint to set a display name for the current user"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    if len(name) > 50:
        return jsonify({'error': 'Name too long (max 50 characters)'}), 400

    # Get the user's IP
    user_ip = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        user_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()

    set_user_name(user_ip, name)

    return jsonify({'success': True, 'name': name, 'ip': user_ip})

@app.route('/api/server-info')
def server_info():
    """API endpoint to get server network information"""
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except (OSError, socket.error) as e:
        logger.warning(f"Could not detect local IP: {e}")
        local_ip = "Unable to detect"

    # Get Tailscale IP
    try:
        result = subprocess.run(['tailscale', 'ip', '-4'], capture_output=True, text=True, timeout=2)
        tailscale_ip = result.stdout.strip() if result.returncode == 0 else "Not available"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning(f"Could not detect Tailscale IP: {e}")
        tailscale_ip = "Not available"

    return jsonify({
        'local_ip': local_ip,
        'tailscale_ip': tailscale_ip,
        'port': 5000
    })

@app.route('/api/storage')
def storage_info():
    """API endpoint to get storage usage statistics"""
    try:
        storage = calculate_storage_usage()

        # Format for human readability
        def format_bytes(bytes_val):
            """Convert bytes to human-readable format"""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.2f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.2f} TB"

        # Check if approaching quota
        is_warning = storage['quota_used_percent'] >= (QUOTA_WARNING_THRESHOLD * 100)

        return success_response(data={
            'total_bytes': storage['total_bytes'],
            'total_formatted': format_bytes(storage['total_bytes']),
            'images_bytes': storage['images_bytes'],
            'images_formatted': format_bytes(storage['images_bytes']),
            'thumbnails_bytes': storage['thumbnails_bytes'],
            'thumbnails_formatted': format_bytes(storage['thumbnails_bytes']),
            'quota_bytes': storage['quota_bytes'],
            'quota_formatted': format_bytes(storage['quota_bytes']),
            'quota_used_percent': round(storage['quota_used_percent'], 2),
            'quota_available_bytes': storage['quota_available_bytes'],
            'quota_available_formatted': format_bytes(storage['quota_available_bytes']),
            'image_count': storage['image_count'],
            'thumbnail_count': storage['thumbnail_count'],
            'is_warning': is_warning,
            'warning_threshold_percent': QUOTA_WARNING_THRESHOLD * 100
        })
    except Exception as e:
        logger.error(f"Error getting storage info: {e}", exc_info=True)
        return error_response('Failed to retrieve storage information', 'STORAGE_ERROR', 500)

@app.route('/api/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_file():
    """API endpoint to handle image uploads"""
    try:
        if 'file' not in request.files:
            return error_response('No file provided', 'NO_FILE', 400)

        file = request.files['file']

        if file.filename == '':
            return error_response('No file selected', 'EMPTY_FILENAME', 400)

        if not allowed_file(file.filename):
            return error_response(
                'File type not allowed. Use PNG, JPG, GIF, or BMP',
                'INVALID_FILE_TYPE',
                400
            )

        # Check storage quota before accepting upload
        storage = calculate_storage_usage()

        # Seek to end to get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset to beginning for actual save

        if storage['quota_available_bytes'] < file_size:
            used_gb = storage['total_bytes'] / (1024**3)
            quota_gb = STORAGE_QUOTA / (1024**3)
            return error_response(
                f'Storage quota exceeded. Using {used_gb:.2f} GB of {quota_gb:.2f} GB. Please delete some images.',
                'QUOTA_EXCEEDED',
                507  # HTTP 507 Insufficient Storage
            )

        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Validate that the file is actually a valid image
        is_valid, error_msg = validate_image_file(filepath)
        if not is_valid:
            # Remove the invalid file
            try:
                os.remove(filepath)
            except OSError as e:
                logger.error(f"Failed to remove invalid file {filepath}: {e}")
            return error_response(error_msg, 'INVALID_IMAGE', 400)

        # Generate thumbnail
        thumb_success, thumb_error = generate_thumbnail(filename)
        if not thumb_success:
            # Log the error but don't fail the upload
            logger.warning(f"Failed to generate thumbnail for {filename}: {thumb_error}")

        # Get uploader's IP address
        uploader_ip = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            # If behind a proxy, get the real IP
            uploader_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()

        # Get allowed devices from form data
        allowed_devices = []
        if 'allowed_devices' in request.form:
            try:
                allowed_devices = json.loads(request.form['allowed_devices'])
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse allowed_devices JSON: {e}")
                # If parsing fails, just use empty list

        # Store metadata with allowed devices
        add_image_metadata(filename, uploader_ip, allowed_devices)

        logger.info(f"Image uploaded successfully: {filename} by {uploader_ip}")

        return success_response(
            data={
                'filename': filename,
                'uploader_ip': uploader_ip
            },
            message='Image uploaded successfully'
        )

    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}", exc_info=True)
        return error_response(
            'An unexpected error occurred during upload',
            'UPLOAD_ERROR',
            500
        )

@app.route('/api/delete/<filename>', methods=['DELETE'])
@limiter.limit("60 per minute")
def delete_image(filename):
    """API endpoint to delete an image"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(filepath):
            return error_response('File not found', 'FILE_NOT_FOUND', 404)

        # Remove the image file
        os.remove(filepath)

        # Remove thumbnail if it exists
        thumb_path = os.path.join(THUMBNAILS_FOLDER, filename)
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except OSError as e:
                logger.warning(f"Failed to remove thumbnail {thumb_path}: {e}")

        # Remove metadata
        remove_image_metadata(filename)

        # If this was the current image, clear it
        if get_current_image() == filename:
            set_current_image(None)

        logger.info(f"Image deleted successfully: {filename}")
        return success_response(message='Image deleted successfully')

    except OSError as e:
        logger.error(f"Failed to delete image {filename}: {e}")
        return error_response(f'Failed to delete file: {str(e)}', 'DELETE_ERROR', 500)
    except Exception as e:
        logger.error(f"Unexpected error deleting image {filename}: {e}", exc_info=True)
        return error_response(
            'An unexpected error occurred during deletion',
            'DELETE_ERROR',
            500
        )

@app.route('/api/display/<filename>', methods=['POST'])
@limiter.limit("60 per minute")
def display_image(filename):
    """API endpoint to display an image on the e-paper"""
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Call the display script using subprocess for security
        display_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'display_image.py')
        result = subprocess.run(
            ['python3', display_script, filepath],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            set_current_image(filename)
            return jsonify({'success': True, 'message': 'Image displayed on e-paper'})
        else:
            error_msg = result.stderr.strip() if result.stderr else 'Failed to display image'
            return jsonify({'error': error_msg}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Display operation timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Device Management API Endpoints

@app.route('/api/devices/register', methods=['POST'])
@limiter.limit("60 per minute")
def register_device_endpoint():
    """API endpoint to register or update a device"""
    data = request.get_json()

    device_id = data.get('device_id', '').strip()
    name = data.get('name', '').strip()
    device_type = data.get('device_type', 'display').strip()
    metadata = data.get('metadata', {})

    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400

    if not name:
        return jsonify({'error': 'name is required'}), 400

    if len(name) > 100:
        return jsonify({'error': 'Name too long (max 100 characters)'}), 400

    is_new = register_device(device_id, name, device_type, metadata)

    return jsonify({
        'success': True,
        'device_id': device_id,
        'is_new': is_new,
        'message': 'Device registered successfully' if is_new else 'Device updated successfully'
    })

@app.route('/api/devices')
def list_devices():
    """API endpoint to list all registered devices"""
    devices = get_all_devices()
    # Convert to list format with device_id included
    devices_list = [
        {'device_id': device_id, **device_data}
        for device_id, device_data in devices.items()
    ]
    return jsonify({'devices': devices_list})

@app.route('/api/devices/<device_id>', methods=['DELETE'])
@limiter.limit("60 per minute")
def delete_device_endpoint(device_id):
    """API endpoint to delete a device"""
    if delete_device(device_id):
        return jsonify({'success': True, 'message': 'Device deleted'})
    else:
        return jsonify({'error': 'Device not found'}), 404

@app.route('/api/devices/<device_id>/images')
def get_device_images(device_id):
    """API endpoint to get all images for a specific device"""
    # Update last seen
    update_device_last_seen(device_id)

    # Check if device exists
    device = get_device(device_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    images = get_images_for_device(device_id)
    return jsonify({
        'device_id': device_id,
        'device_name': device['name'],
        'images': images,
        'count': len(images)
    })

@app.route('/api/devices/<device_id>/next')
def get_next_image_for_device(device_id):
    """API endpoint to get next random image for a device"""
    # Update last seen
    update_device_last_seen(device_id)

    # Check if device exists
    device = get_device(device_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    images = get_images_for_device(device_id)

    if not images:
        return jsonify({'error': 'No images available for this device'}), 404

    # Get current image from state (if this device tracks it)
    current = get_current_image()

    # Filter out current image if possible
    available = [img for img in images if img['filename'] != current]
    if not available:
        available = images  # If all we have is the current image, use it

    # Select random image
    next_image = random.choice(available)

    return jsonify({
        'device_id': device_id,
        'image': next_image,
        'url': f"/uploads/{next_image['filename']}"
    })

@app.route('/api/images/<filename>/devices', methods=['POST'])
@limiter.limit("60 per minute")
def update_image_devices_endpoint(filename):
    """API endpoint to update which devices can view an image"""
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Image not found'}), 404

    data = request.get_json()
    allowed_devices = data.get('allowed_devices', [])

    if not isinstance(allowed_devices, list):
        return jsonify({'error': 'allowed_devices must be an array'}), 400

    # Validate that all device IDs exist
    all_devices = get_all_devices()
    for device_id in allowed_devices:
        if device_id not in all_devices:
            return jsonify({'error': f'Device not found: {device_id}'}), 404

    if update_image_devices(filename, allowed_devices):
        return jsonify({
            'success': True,
            'filename': filename,
            'allowed_devices': allowed_devices,
            'message': 'Image device permissions updated'
        })
    else:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/uploads/<filename>')
@limiter.exempt  # Exempt image serving from rate limiting
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/thumbnails/<filename>')
@limiter.exempt  # Exempt thumbnails from rate limiting for smooth gallery browsing
def thumbnail_file(filename):
    """Serve thumbnail images"""
    filename = secure_filename(filename)
    thumb_path = os.path.join(THUMBNAILS_FOLDER, filename)

    # If thumbnail doesn't exist, try to generate it
    if not os.path.exists(thumb_path):
        source_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(source_path):
            success, error = generate_thumbnail(filename)
            if not success:
                # If thumbnail generation fails, serve the original image
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Serve thumbnail if it exists, otherwise serve original
    if os.path.exists(thumb_path):
        return send_from_directory(THUMBNAILS_FOLDER, filename)
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/images/<filename>/rotate', methods=['POST'])
@limiter.limit("60 per minute")
def rotate_image(filename):
    """API endpoint to rotate an image"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(filepath):
            return error_response('Image not found', 'FILE_NOT_FOUND', 404)

        # Get rotation angle from request
        data = request.get_json()
        angle = data.get('angle', 90)

        # Validate angle
        if angle not in [90, 180, 270]:
            return error_response(
                'Invalid rotation angle. Must be 90, 180, or 270',
                'INVALID_ANGLE',
                400
            )

        # Rotate the image
        try:
            with Image.open(filepath) as img:
                # Convert angle to Pillow's rotation direction
                # Pillow rotates counter-clockwise, so we need to negate for clockwise rotation
                # For UI: 90 = rotate right, 180 = flip, 270 = rotate left
                rotated = img.rotate(-angle, expand=True)

                # Save the rotated image
                # Preserve format and quality
                save_kwargs = {}
                if img.format == 'JPEG':
                    save_kwargs = {'quality': 95, 'optimize': True}
                elif img.format == 'PNG':
                    save_kwargs = {'optimize': True}

                rotated.save(filepath, format=img.format, **save_kwargs)

        except (IOError, OSError) as e:
            logger.error(f"Failed to rotate image {filename}: {e}")
            return error_response(
                f'Failed to rotate image: {str(e)}',
                'ROTATION_ERROR',
                500
            )

        # Regenerate thumbnail
        thumb_success, thumb_error = generate_thumbnail(filename)
        if not thumb_success:
            logger.warning(f"Failed to regenerate thumbnail after rotation for {filename}: {thumb_error}")
            # Don't fail the request, just log the warning

        logger.info(f"Image rotated successfully: {filename} by {angle} degrees")

        return success_response(
            data={'filename': filename, 'angle': angle},
            message='Image rotated successfully'
        )

    except Exception as e:
        logger.error(f"Unexpected error rotating image {filename}: {e}", exc_info=True)
        return error_response(
            'An unexpected error occurred during rotation',
            'ROTATION_ERROR',
            500
        )

@app.route('/api/images/bulk-delete', methods=['POST'])
@limiter.limit("60 per minute")
def bulk_delete_images():
    """API endpoint to delete multiple images at once"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])

        if not isinstance(filenames, list):
            return error_response('filenames must be an array', 'INVALID_INPUT', 400)

        if not filenames:
            return error_response('No filenames provided', 'EMPTY_LIST', 400)

        if len(filenames) > 100:
            return error_response('Cannot delete more than 100 images at once', 'TOO_MANY_FILES', 400)

        deleted_count = 0
        errors = []

        for filename in filenames:
            try:
                filename = secure_filename(filename)
                if not filename:
                    errors.append({'filename': filename, 'error': 'Invalid filename'})
                    continue

                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                thumb_path = os.path.join(THUMBNAILS_FOLDER, filename)

                # Delete main image
                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted_count += 1

                # Delete thumbnail
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)

                # Remove from database
                db.delete_image(filename)

                logger.info(f"Bulk deleted image: {filename}")

            except (OSError, IOError) as e:
                logger.error(f"Failed to delete image {filename}: {e}")
                errors.append({'filename': filename, 'error': str(e)})
            except Exception as e:
                logger.error(f"Unexpected error deleting image {filename}: {e}", exc_info=True)
                errors.append({'filename': filename, 'error': 'Unexpected error'})

        # Prepare response
        response_data = {
            'deleted_count': deleted_count,
            'requested_count': len(filenames),
            'errors': errors
        }

        if deleted_count == 0:
            return error_response(
                'Failed to delete any images',
                'BULK_DELETE_FAILED',
                500
            )
        elif errors:
            # Partial success
            return jsonify({
                'success': True,
                'data': response_data,
                'message': f'Deleted {deleted_count} of {len(filenames)} images (some errors occurred)'
            })
        else:
            # Full success
            return success_response(
                data=response_data,
                message=f'Successfully deleted {deleted_count} images'
            )

    except Exception as e:
        logger.error(f"Unexpected error in bulk delete: {e}", exc_info=True)
        return error_response(
            'An unexpected error occurred during bulk delete',
            'BULK_DELETE_ERROR',
            500
        )

@app.route('/api/images/bulk-update-devices', methods=['POST'])
@limiter.limit("60 per minute")
def bulk_update_devices():
    """API endpoint to update device permissions for multiple images at once"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        allowed_devices = data.get('allowed_devices', [])

        if not isinstance(filenames, list):
            return error_response('filenames must be an array', 'INVALID_INPUT', 400)

        if not isinstance(allowed_devices, list):
            return error_response('allowed_devices must be an array', 'INVALID_INPUT', 400)

        if not filenames:
            return error_response('No filenames provided', 'EMPTY_LIST', 400)

        if len(filenames) > 100:
            return error_response('Cannot update more than 100 images at once', 'TOO_MANY_FILES', 400)

        # Validate that all device IDs exist
        all_devices = get_all_devices()
        for device_id in allowed_devices:
            if device_id not in all_devices:
                return error_response(f'Device not found: {device_id}', 'DEVICE_NOT_FOUND', 404)

        updated_count = 0
        errors = []

        for filename in filenames:
            try:
                filename = secure_filename(filename)
                if not filename:
                    errors.append({'filename': filename, 'error': 'Invalid filename'})
                    continue

                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                if not os.path.exists(filepath):
                    errors.append({'filename': filename, 'error': 'Image not found'})
                    continue

                # Update device permissions
                if update_image_devices(filename, allowed_devices):
                    updated_count += 1
                    logger.info(f"Bulk updated devices for image: {filename}")
                else:
                    errors.append({'filename': filename, 'error': 'Failed to update'})

            except Exception as e:
                logger.error(f"Unexpected error updating devices for {filename}: {e}", exc_info=True)
                errors.append({'filename': filename, 'error': 'Unexpected error'})

        # Prepare response
        response_data = {
            'updated_count': updated_count,
            'requested_count': len(filenames),
            'allowed_devices': allowed_devices,
            'errors': errors
        }

        if updated_count == 0:
            return error_response(
                'Failed to update any images',
                'BULK_UPDATE_FAILED',
                500
            )
        elif errors:
            # Partial success
            return jsonify({
                'success': True,
                'data': response_data,
                'message': f'Updated {updated_count} of {len(filenames)} images (some errors occurred)'
            })
        else:
            # Full success
            return success_response(
                data=response_data,
                message=f'Successfully updated {updated_count} images'
            )

    except Exception as e:
        logger.error(f"Unexpected error in bulk update: {e}", exc_info=True)
        return error_response(
            'An unexpected error occurred during bulk update',
            'BULK_UPDATE_ERROR',
            500
        )

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(THUMBNAILS_FOLDER, exist_ok=True)

    # Initialize database if it doesn't exist
    if not os.path.exists(db.DB_FILE):
        print("Initializing database...")
        db.init_database()
        print(f"Database created: {db.DB_FILE}")
    else:
        print(f"Using existing database: {db.DB_FILE}")

    # SSL certificate paths
    cert_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert.pem')
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key.pem')

    # Run on all interfaces so it's accessible from network
    # Use HTTPS if certificates exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=(cert_file, key_file))
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)
