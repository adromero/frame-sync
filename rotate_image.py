#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import random
from datetime import datetime
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STATE_FILE = os.path.join(BASE_DIR, 'state.json')
DISPLAY_SCRIPT = os.path.join(BASE_DIR, 'display_image.py')
METADATA_FILE = os.path.join(BASE_DIR, 'metadata.json')
DEVICES_FILE = os.path.join(BASE_DIR, 'devices.json')
DEVICE_ID_FILE = os.path.join(BASE_DIR, 'epaper_device_id.txt')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# E-Paper device configuration
EPAPER_DEVICE_NAME = "E-Paper Frame"
EPAPER_DEVICE_TYPE = "epaper"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_or_create_device_id():
    """Get the device ID for this e-paper frame, creating one if it doesn't exist"""
    if os.path.exists(DEVICE_ID_FILE):
        try:
            with open(DEVICE_ID_FILE, 'r') as f:
                device_id = f.read().strip()
                if device_id:
                    return device_id
        except:
            pass

    # Generate a new device ID
    device_id = str(uuid.uuid4())
    with open(DEVICE_ID_FILE, 'w') as f:
        f.write(device_id)
    logger.info(f"Generated new device ID: {device_id}")
    return device_id

def register_epaper_device():
    """Register this e-paper device in the device registry"""
    device_id = get_or_create_device_id()

    # Load or create devices registry
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, 'r') as f:
                devices_data = json.load(f)
        except:
            devices_data = {'devices': {}}
    else:
        devices_data = {'devices': {}}

    # Register or update device
    is_new = device_id not in devices_data['devices']

    if is_new:
        devices_data['devices'][device_id] = {
            'name': EPAPER_DEVICE_NAME,
            'device_type': EPAPER_DEVICE_TYPE,
            'registered': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'metadata': {}
        }
        logger.info(f"Registered new e-paper device: {device_id}")

        # On first registration, assign all existing images to this device
        assign_all_images_to_device(device_id)
    else:
        devices_data['devices'][device_id]['last_seen'] = datetime.now().isoformat()

    # Save devices registry
    with open(DEVICES_FILE, 'w') as f:
        json.dump(devices_data, f, indent=2)

    return device_id

def assign_all_images_to_device(device_id):
    """Assign all existing images to a newly registered device (for backward compatibility)"""
    metadata = load_metadata()
    updated = False

    for filename in metadata['images']:
        allowed_devices = metadata['images'][filename].get('allowed_devices', [])
        # Add this device if it's not already in the list
        if device_id not in allowed_devices:
            allowed_devices.append(device_id)
            metadata['images'][filename]['allowed_devices'] = allowed_devices
            updated = True

    if updated:
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Assigned {len(metadata['images'])} existing images to device {device_id}")

def load_metadata():
    """Load image metadata from file"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'images': {}, 'users': {}}

def get_images_for_device(device_id):
    """Get all images that this device is allowed to view"""
    metadata = load_metadata()
    images = []

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                img_metadata = metadata['images'].get(filename, {})
                allowed_devices = img_metadata.get('allowed_devices', [])

                # Check if this device is allowed to view this image
                if device_id in allowed_devices:
                    images.append(filename)

    return sorted(images)

def get_current_image():
    """Get the currently displayed image from state file"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return state.get('current_image')
        except:
            pass
    return None

def set_current_image(filename):
    """Save the currently displayed image to state file"""
    state = {
        'current_image': filename,
        'updated': datetime.now().isoformat()
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def get_all_images():
    """Get list of all uploaded images"""
    images = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                images.append(filename)
    return sorted(images)

def get_next_image(device_id):
    """Get the next image to display (random selection excluding current)"""
    # Get images this device is allowed to view
    all_images = get_images_for_device(device_id)

    if not all_images:
        logger.info("No images available for this device to display")
        return None

    if len(all_images) == 1:
        logger.info("Only one image available")
        return all_images[0]

    current = get_current_image()

    # Filter out current image to avoid showing the same one
    available = [img for img in all_images if img != current]

    if not available:
        available = all_images

    # Pick a random image
    next_image = random.choice(available)
    logger.info(f"Selected next image: {next_image}")
    return next_image

def rotate_image():
    """Rotate to the next image and display it"""
    try:
        # Register this device
        device_id = register_epaper_device()
        logger.info(f"E-Paper device ID: {device_id}")

        next_image = get_next_image(device_id)

        if not next_image:
            logger.warning("No images to display")
            return 1

        image_path = os.path.join(UPLOAD_FOLDER, next_image)

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return 1

        logger.info(f"Displaying: {next_image}")

        # Call the display script using subprocess for security
        try:
            result = subprocess.run(
                ['python3', DISPLAY_SCRIPT, image_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                set_current_image(next_image)
                logger.info("Image rotation successful")
                return 0
            else:
                error_msg = result.stderr.strip() if result.stderr else 'Unknown error'
                logger.error(f"Failed to display image: {error_msg}")
                return 1

        except subprocess.TimeoutExpired:
            logger.error("Display operation timed out")
            return 1

    except Exception as e:
        logger.error(f"Error during rotation: {str(e)}")
        return 1

if __name__ == '__main__':
    exit_code = rotate_image()
    sys.exit(exit_code)
