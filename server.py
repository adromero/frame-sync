#!/usr/bin/env python3
import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import random

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state.json')
METADATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metadata.json')
DEVICES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devices.json')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Enable CORS for all routes
CORS(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_metadata():
    """Load image metadata from file"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'images': {}, 'users': {}}

def save_metadata(metadata):
    """Save image metadata to file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def add_image_metadata(filename, uploader_ip, allowed_devices=None):
    """Add metadata for a newly uploaded image"""
    metadata = load_metadata()
    metadata['images'][filename] = {
        'uploader_ip': uploader_ip,
        'upload_time': datetime.now().isoformat(),
        'allowed_devices': allowed_devices if allowed_devices is not None else []
    }
    save_metadata(metadata)

def remove_image_metadata(filename):
    """Remove metadata for a deleted image"""
    metadata = load_metadata()
    if filename in metadata['images']:
        del metadata['images'][filename]
        save_metadata(metadata)

def set_user_name(ip, name):
    """Set a display name for a user IP"""
    metadata = load_metadata()
    if 'users' not in metadata:
        metadata['users'] = {}
    metadata['users'][ip] = {
        'name': name,
        'updated': datetime.now().isoformat()
    }
    save_metadata(metadata)

def get_user_name(ip):
    """Get the display name for a user IP, or return the IP if no name set"""
    metadata = load_metadata()
    if 'users' in metadata and ip in metadata['users']:
        return metadata['users'][ip].get('name', ip)
    return ip

def get_all_users():
    """Get list of all unique uploader IPs with their names"""
    metadata = load_metadata()
    users = set()
    for img_data in metadata['images'].values():
        users.add(img_data['uploader_ip'])

    # Build user list with names
    user_list = []
    for ip in sorted(list(users)):
        user_list.append({
            'ip': ip,
            'name': get_user_name(ip)
        })
    return user_list

def get_image_list(filter_user=None):
    """Get list of uploaded images with metadata

    Args:
        filter_user: Optional IP address to filter images by uploader
    """
    metadata = load_metadata()
    images = []

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                stat = os.stat(filepath)

                # Get uploader info from metadata
                img_metadata = metadata['images'].get(filename, {})
                uploader_ip = img_metadata.get('uploader_ip', 'unknown')

                # Apply user filter if specified
                if filter_user and uploader_ip != filter_user:
                    continue

                images.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'uploaded': img_metadata.get('upload_time', datetime.fromtimestamp(stat.st_mtime).isoformat()),
                    'uploader_ip': uploader_ip,
                    'uploader_name': get_user_name(uploader_ip),
                    'allowed_devices': img_metadata.get('allowed_devices', [])
                })

    images.sort(key=lambda x: x['uploaded'], reverse=True)
    return images

def get_current_image():
    """Get the currently displayed image"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return state.get('current_image')
        except:
            pass
    return None

def set_current_image(filename):
    """Set the currently displayed image"""
    state = {'current_image': filename, 'updated': datetime.now().isoformat()}
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

# Device Management Functions

def load_devices():
    """Load device registry from file"""
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'devices': {}}

def save_devices(devices_data):
    """Save device registry to file"""
    with open(DEVICES_FILE, 'w') as f:
        json.dump(devices_data, f, indent=2)

def register_device(device_id, name, device_type='display', metadata=None):
    """Register or update a device"""
    devices_data = load_devices()

    is_new = device_id not in devices_data['devices']

    if is_new:
        devices_data['devices'][device_id] = {
            'name': name,
            'device_type': device_type,
            'registered': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
    else:
        # Update existing device
        devices_data['devices'][device_id]['name'] = name
        devices_data['devices'][device_id]['device_type'] = device_type
        devices_data['devices'][device_id]['last_seen'] = datetime.now().isoformat()
        if metadata:
            devices_data['devices'][device_id]['metadata'] = metadata

    save_devices(devices_data)
    return is_new

def update_device_last_seen(device_id):
    """Update the last seen timestamp for a device"""
    devices_data = load_devices()
    if device_id in devices_data['devices']:
        devices_data['devices'][device_id]['last_seen'] = datetime.now().isoformat()
        save_devices(devices_data)

def get_device(device_id):
    """Get a specific device by ID"""
    devices_data = load_devices()
    return devices_data['devices'].get(device_id)

def get_all_devices():
    """Get all registered devices"""
    devices_data = load_devices()
    return devices_data['devices']

def delete_device(device_id):
    """Remove a device from the registry"""
    devices_data = load_devices()
    if device_id in devices_data['devices']:
        del devices_data['devices'][device_id]
        save_devices(devices_data)
        return True
    return False

def update_image_devices(filename, allowed_devices):
    """Update the list of devices allowed to view an image"""
    metadata = load_metadata()
    if filename in metadata['images']:
        metadata['images'][filename]['allowed_devices'] = allowed_devices
        save_metadata(metadata)
        return True
    return False

def get_images_for_device(device_id):
    """Get all images that a specific device is allowed to view"""
    metadata = load_metadata()
    images = []

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                img_metadata = metadata['images'].get(filename, {})
                allowed_devices = img_metadata.get('allowed_devices', [])

                # Check if this device is allowed to view this image
                if device_id in allowed_devices:
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    stat = os.stat(filepath)
                    uploader_ip = img_metadata.get('uploader_ip', 'unknown')

                    images.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'uploaded': img_metadata.get('upload_time', datetime.fromtimestamp(stat.st_mtime).isoformat()),
                        'uploader_ip': uploader_ip,
                        'uploader_name': get_user_name(uploader_ip)
                    })

    images.sort(key=lambda x: x['uploaded'], reverse=True)
    return images

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
    """API endpoint to list all uploaded images"""
    filter_user = request.args.get('user')  # Optional filter by user IP
    images = get_image_list(filter_user=filter_user)
    current = get_current_image()
    return jsonify({'images': images, 'current_image': current})

@app.route('/api/users')
def list_users():
    """API endpoint to list all unique uploaders"""
    users = get_all_users()
    # Count images per user
    metadata = load_metadata()
    user_counts = {}
    for img_data in metadata['images'].values():
        ip = img_data['uploader_ip']
        user_counts[ip] = user_counts.get(ip, 0) + 1

    users_with_counts = [{'ip': user['ip'], 'name': user['name'], 'image_count': user_counts.get(user['ip'], 0)} for user in users]
    return jsonify({'users': users_with_counts})

@app.route('/api/user/name', methods=['POST'])
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
    import socket
    import subprocess

    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "Unable to detect"

    # Get Tailscale IP
    try:
        result = subprocess.run(['tailscale', 'ip', '-4'], capture_output=True, text=True, timeout=2)
        tailscale_ip = result.stdout.strip() if result.returncode == 0 else "Not available"
    except:
        tailscale_ip = "Not available"

    return jsonify({
        'local_ip': local_ip,
        'tailscale_ip': tailscale_ip,
        'port': 5000
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """API endpoint to handle image uploads"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use PNG, JPG, GIF, or BMP'}), 400

    filename = secure_filename(file.filename)
    # Add timestamp to avoid conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

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
        except json.JSONDecodeError:
            pass  # If parsing fails, just use empty list

    # Store metadata with allowed devices
    add_image_metadata(filename, uploader_ip, allowed_devices)

    return jsonify({
        'success': True,
        'filename': filename,
        'message': 'Image uploaded successfully',
        'uploader_ip': uploader_ip
    })

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    """API endpoint to delete an image"""
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        os.remove(filepath)
        # Remove metadata
        remove_image_metadata(filename)
        # If this was the current image, clear it
        if get_current_image() == filename:
            set_current_image(None)
        return jsonify({'success': True, 'message': 'Image deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/display/<filename>', methods=['POST'])
def display_image(filename):
    """API endpoint to display an image on the e-paper"""
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Call the display script
        display_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'display_image.py')
        result = os.system(f'python3 "{display_script}" "{filepath}"')

        if result == 0:
            set_current_image(filename)
            return jsonify({'success': True, 'message': 'Image displayed on e-paper'})
        else:
            return jsonify({'error': 'Failed to display image'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Device Management API Endpoints

@app.route('/api/devices/register', methods=['POST'])
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
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # SSL certificate paths
    cert_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert.pem')
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key.pem')

    # Run on all interfaces so it's accessible from network
    # Use HTTPS if certificates exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=(cert_file, key_file))
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)
