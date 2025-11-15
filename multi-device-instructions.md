# Multi-Device Support

FrameSync supports serving images to multiple display devices on your local network or Tailscale network. Each image can be assigned to specific devices, giving you control over what displays where. Whether you're using e-paper displays, tablets, smart displays, or any device that can fetch images via HTTP, FrameSync provides a unified API for managing your photo distribution.

## Overview

The system uses a device registry where each device has:
- A unique UUID identifier
- A human-readable name
- A device type (e.g., "epaper", "tablet", "lcd", "display")
- Registration and last-seen timestamps

Images are assigned to devices through the web interface or API. Only devices that have been granted access to an image can retrieve it.

## Architecture

### Device Registration
- Devices self-register with a UUID they generate
- The primary e-paper display (if configured) automatically registers on first run and is assigned all existing images
- Additional display devices can be added through the web UI or API
- Any device type can be registered: e-paper displays, tablets, smart displays, LCD screens, etc.

### Image Permissions
- When uploading images, you select which devices should receive them via the upload flow
- You can also update device permissions after upload through the image detail modal
- If no devices are selected during upload, the image won't be assigned to any devices
- This gives you fine-grained control over content distribution across your displays

## Web Interface

### Managing Devices

1. **Add a Device**:
   - Navigate to the "Devices" section
   - Enter a device name (e.g., "Living Room Display")
   - Click "Add New Device"
   - A UUID will be automatically generated for the device

2. **Assign Images on Upload**:
   - Select or drag images to the upload area
   - A device selection panel will appear with all registered devices
   - Check the devices that should receive these images (or select "All Displays")
   - Click "Upload" to confirm, or "Cancel" to abort
   - Images will be uploaded with the selected device permissions

3. **Update Image Permissions After Upload**:
   - Click on any image in the gallery to open the modal
   - In the "Allowed Devices" section, check/uncheck devices
   - Click "Save Devices" to update permissions

4. **Delete a Device**:
   - Click the "Delete" button next to any device in the Devices section
   - This removes the device but does not delete any images

## API Reference

Base URL: `http://YOUR_IP:5000` or `https://YOUR_IP:5000` (if HTTPS is configured)

**Note**: All API endpoints support both HTTP and HTTPS depending on your server configuration.

### Device Management

#### Register a Device
```bash
POST /api/devices/register
Content-Type: application/json

{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Living Room Display",
  "device_type": "display"
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_new": true,
  "message": "Device registered successfully"
}
```

#### List All Devices
```bash
GET /api/devices
```

**Response:**
```json
{
  "devices": [
    {
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Living Room Display",
      "device_type": "display",
      "registered": "2025-11-13T18:00:00.000000",
      "last_seen": "2025-11-13T18:05:00.000000",
      "metadata": {}
    }
  ]
}
```

#### Delete a Device
```bash
DELETE /api/devices/{device_id}
```

### Image Retrieval

#### Get All Images for a Device
```bash
GET /api/devices/{device_id}/images
```

Returns all images that the specified device is allowed to view.

**Response:**
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "Living Room Display",
  "count": 15,
  "images": [
    {
      "filename": "photo_20251113_123456.jpg",
      "size": 2048576,
      "uploaded": "2025-11-13T12:34:56.000000",
      "uploader_ip": "192.168.1.100",
      "uploader_name": "Dad"
    }
  ]
}
```

#### Get Next Random Image
```bash
GET /api/devices/{device_id}/next
```

Returns a random image (excluding the currently displayed one if tracked).

**Response:**
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "image": {
    "filename": "photo_20251113_123456.jpg",
    "size": 2048576,
    "uploaded": "2025-11-13T12:34:56.000000",
    "uploader_ip": "192.168.1.100",
    "uploader_name": "Dad"
  },
  "url": "/uploads/photo_20251113_123456.jpg"
}
```

#### Download Image
```bash
GET /uploads/{filename}
```

Returns the raw image file.

### Image Permission Management

#### Update Device Access for an Image
```bash
POST /api/images/{filename}/devices
Content-Type: application/json

{
  "allowed_devices": [
    "550e8400-e29b-41d4-a716-446655440000",
    "another-device-uuid-here"
  ]
}
```

## Integration Examples

### Python Example

```python
import requests
import uuid
import time

# Configuration
SERVER_URL = "http://192.168.1.100:5000"
DEVICE_ID = str(uuid.uuid4())  # Generate once and save
DEVICE_NAME = "My Display Device"

# Register device
def register_device():
    response = requests.post(
        f"{SERVER_URL}/api/devices/register",
        json={
            "device_id": DEVICE_ID,
            "name": DEVICE_NAME,
            "device_type": "display"
        }
    )
    print(f"Device registered: {response.json()}")

# Get next image
def get_next_image():
    response = requests.get(f"{SERVER_URL}/api/devices/{DEVICE_ID}/next")
    if response.status_code == 200:
        data = response.json()
        image_url = f"{SERVER_URL}{data['url']}"
        return image_url, data['image']['filename']
    return None, None

# Download image
def download_image(image_url, filename):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    return False

# Main loop
register_device()

while True:
    image_url, filename = get_next_image()
    if image_url:
        print(f"Downloading: {filename}")
        download_image(image_url, f"/tmp/current_image.jpg")
        # Display the image here
    time.sleep(3600)  # Check every hour
```

### Bash/curl Example

```bash
#!/bin/bash

SERVER="http://192.168.1.100:5000"
DEVICE_ID="550e8400-e29b-41d4-a716-446655440000"
DEVICE_NAME="Kitchen Tablet"

# Register device
curl -X POST "$SERVER/api/devices/register" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"$DEVICE_ID\",\"name\":\"$DEVICE_NAME\",\"device_type\":\"tablet\"}"

# Get next image
IMAGE_URL=$(curl -s "$SERVER/api/devices/$DEVICE_ID/next" | jq -r '.url')

# Download image
curl -s "$SERVER$IMAGE_URL" -o /tmp/current_image.jpg

# Display the image (example with feh)
feh --fullscreen /tmp/current_image.jpg
```

## Data Storage

### Files Created
- `devices.json` - Device registry
- `metadata.json` - Image metadata including device assignments
- `epaper_device_id.txt` - Persistent UUID for the e-paper device

### Device Registry Format
```json
{
  "devices": {
    "device-uuid": {
      "name": "Device Name",
      "device_type": "display",
      "registered": "2025-11-13T18:00:00.000000",
      "last_seen": "2025-11-13T18:05:00.000000",
      "metadata": {}
    }
  }
}
```

### Image Metadata Format
```json
{
  "images": {
    "filename.jpg": {
      "uploader_ip": "192.168.1.100",
      "upload_time": "2025-11-13T12:34:56.000000",
      "allowed_devices": ["device-uuid-1", "device-uuid-2"]
    }
  }
}
```

## Security Considerations

- No authentication is currently implemented
- All devices on your network can access the API
- Recommend using Tailscale for secure remote access
- Consider implementing authentication if exposing to untrusted networks

## Backward Compatibility

- If you have an e-paper display configured, all existing functionality is fully preserved
- On first run, the e-paper device auto-registers and is assigned all existing images
- The hourly rotation continues to work as before for e-paper displays
- Legacy images without device assignments will be automatically assigned to the e-paper device (if configured)
- The system works perfectly fine without any e-paper display - you can use it purely as a photo server for other display types

## Troubleshooting

### Device Not Seeing Images
- Check that the device is registered: `GET /api/devices`
- Verify images are assigned to the device: `GET /api/devices/{device_id}/images`
- Use the web interface to assign images to the device

### API Returns 404
- Confirm the device ID exists in the registry
- Check that the server is running: `sudo systemctl status epaper-frame.service`

### Images Not Rotating on E-Paper
- Check the e-paper device ID: `cat epaper_device_id.txt`
- Verify images are assigned to it: Check `metadata.json`
- Test the rotation script: `python3 rotate_image.py`
