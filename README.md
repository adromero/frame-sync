# FrameSync

A web-based photo frame server that can serve images to multiple displays on your local network. Originally designed for Waveshare 5.65" 7-color e-paper displays, it now supports any display device that can fetch images via HTTP API.

## Features

- 📱 Mobile-friendly web interface for uploading photos
- 👥 Multi-user support with IP-based user tracking and custom display names
- 🔍 Filter images by user (all photos, my photos, or specific users)
- 📺 Multi-device support - serve images to any display via HTTP API
- 🔐 Per-image device permissions - control which displays can see each image
- ✅ Device selection on upload - assign images to displays immediately when uploading
- 🎯 Device management - register, view, and delete display devices through the web UI
- 🔄 Automatic hourly image rotation (for e-paper displays)
- 🎨 Optimized image processing for 7-color e-paper displays
- 🌐 Accessible via local network or Tailscale
- 🚀 Auto-starts on boot via systemd
- 🔒 HTTPS support with SSL certificates
- 🛡️ Rate limiting to prevent abuse (10 uploads/min, 60 API requests/min per IP)
- 📊 Thumbnail generation for faster gallery loading
- 📄 Pagination support for large image collections
- ⚡ Lazy loading with skeleton animations for optimal performance
- 💾 SQLite database for reliable metadata storage
- 📈 Storage quota management with configurable limits
- 🔍 File content validation to prevent malicious uploads
- 📝 Comprehensive error handling and logging
- 🔄 Image rotation - rotate images 90°, 180°, or 270° directly in the web interface

## Hardware Requirements

### Server
- Raspberry Pi (tested on Pi 4) or any Linux server

### Optional: E-Paper Display
- Waveshare 5.65" 7-Color E-Paper Display (600x448)
- Waveshare e-Paper library

### Or: Any Display Device
- Any device that can make HTTP requests and display images (tablets, smart displays, Raspberry Pi with LCD, etc.)

## Setup

### 1. (Optional) Install Waveshare e-Paper Library

Only required if using an e-paper display:

```bash
cd ~
git clone https://github.com/waveshare/e-Paper
```

### 2. Install Python Dependencies

```bash
cd ~/frame-sync
pip3 install -r requirements.txt
```

### 3. (Optional) Setup HTTPS with SSL Certificates

To enable HTTPS, place your SSL certificate files in the project directory:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

The server will automatically use HTTPS if these files exist, otherwise it falls back to HTTP.

### 4. Install Systemd Service

```bash
sudo cp frame-sync.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable frame-sync.service
sudo systemctl start frame-sync.service
```

For e-paper displays with automatic rotation:
```bash
sudo cp epaper-rotate.service /etc/systemd/system/
sudo cp epaper-rotate.timer /etc/systemd/system/
sudo systemctl enable epaper-rotate.timer
sudo systemctl start epaper-rotate.timer
```

### 5. Access the Web Interface

The server runs on port 5000:
- **Local network (HTTP)**: `http://<raspberry-pi-ip>:5000`
- **Local network (HTTPS)**: `https://<raspberry-pi-ip>:5000`
- **Tailscale (HTTP)**: `http://<tailscale-ip>:5000`
- **Tailscale (HTTPS)**: `https://<tailscale-ip>:5000`

## Usage

### Web Interface

#### Uploading Photos

1. Open the web interface on your phone or computer
2. Click or drag images to the upload area
3. **Select which displays should receive the images** using the device selection panel
   - Check individual devices or use "All Displays" to select all
   - Click "Upload" to confirm or "Cancel" to abort
4. Images will be uploaded with the selected device permissions

#### Managing Devices

1. Navigate to the **Devices** section
2. **Add a device**: Enter a name and click "Add New Device" (UUID auto-generated)
3. **View devices**: See all registered devices with their last-seen timestamps
4. **Delete devices**: Remove devices you no longer need

#### Managing Image Permissions

1. Click on any image in the gallery to open the detail modal
2. In the **Allowed Devices** section, check/uncheck devices
3. Click "Save Devices" to update which displays can access the image

#### Rotating Images

1. Click on any image in the gallery to open the detail modal
2. Use the rotation buttons at the bottom of the modal:
   - **↺ 90°** - Rotate counter-clockwise (left)
   - **↻ 180°** - Flip upside down
   - **↻ 90°** - Rotate clockwise (right)
3. The image and thumbnail will update immediately
4. Original image file is permanently rotated

#### Setting Your Display Name

1. After your first upload, your IP address will appear in the "Your Identity" section
2. Click the input field or "Change Name" button
3. Enter your preferred display name (e.g., "Dad", "Mom", "Alex")
4. Click "Save" - your name will now appear instead of your IP address

### Multi-User Features

Each uploader is identified by their IP address and optional display name:

- **Your Identity**: Shows your IP address and allows you to set a custom display name
- **Filter Options**:
  - **All Photos**: View all images from all users
  - **My Photos**: View only images you uploaded
  - **Specific User**: Filter by a specific user (shows name and photo count)
- **Image Attribution**: Each image shows who uploaded it with their display name
- **User List**: The filter dropdown shows all users with their names and photo counts

Perfect for families or roommates sharing photo frames across multiple displays!

### Multi-Device API

Connect any display device to fetch images via the HTTP API. See [multi-device-instructions.md](multi-device-instructions.md) for detailed API documentation and integration examples.

## File Structure

```
frame-sync/
├── server.py                 # Flask web server with multi-user and multi-device support
├── database.py               # SQLite database operations
├── display_image.py          # Display image on e-paper (optional)
├── rotate_image.py           # Hourly rotation logic (optional)
├── templates/
│   └── index.html           # Web interface with device management and upload flow
├── uploads/                 # Uploaded images (gitignored)
│   └── thumbnails/          # Auto-generated thumbnails (gitignored)
├── framesync.db             # SQLite database (gitignored)
├── framesync.log            # Application logs (gitignored)
├── epaper_device_id.txt     # Persistent e-paper device UUID (gitignored)
├── cert.pem                 # SSL certificate (optional, gitignored)
├── key.pem                  # SSL private key (optional, gitignored)
├── frame-sync.service       # Systemd service for web server
├── epaper-rotate.service    # Systemd service for rotation (optional)
├── epaper-rotate.timer      # Systemd timer for hourly rotation (optional)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

### Server Configuration

Edit these settings in `server.py`:
- **Port**: Default is 5000 (line 574-576)
- **Max file size**: 16MB (line 30)
- **Allowed file types**: PNG, JPG, JPEG, GIF, BMP (line 29)
- **Storage quota**: 5GB default (line 32)
- **Rate limits**:
  - Upload endpoint: 10 per minute per IP
  - API endpoints: 60 per minute per IP
  - Global default: 200 per day, 50 per hour

### HTTPS/SSL Configuration

- Place `cert.pem` and `key.pem` in the project root directory
- Server automatically detects and enables HTTPS if certificates exist
- Falls back to HTTP if certificates are not present

### E-Paper Display Configuration (Optional)

Only needed if using a physical e-paper display:
- **Display dimensions**: 600x448 (hardcoded for Waveshare 5.65")
- **Rotation interval**: Edit `epaper-rotate.timer` (default: hourly)
- **Path to e-Paper library**: Update path in `display_image.py` if needed

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status frame-sync.service
sudo systemctl status epaper-rotate.timer  # if using e-paper
```

### View Logs
```bash
journalctl -u frame-sync.service -f
journalctl -u epaper-rotate.service -f  # if using e-paper
```

### Common Issues

**Device selection not working after upload:**
- Make sure you're clicking the "Upload" button after selecting devices
- The device selection panel should appear after choosing files
- Check browser console for any JavaScript errors

**Images not appearing on devices:**
- Verify the device is registered: Check the Devices section in web UI
- Ensure images are assigned to the device: Click image and check "Allowed Devices"
- For API clients: Verify device ID matches exactly

**HTTPS not working:**
- Verify `cert.pem` and `key.pem` exist in the project directory
- Check certificate validity and permissions
- Review logs: `journalctl -u frame-sync.service -f`

**Rate limit exceeded (HTTP 429):**
- Upload limit: 10 images per minute per IP address
- API limit: 60 requests per minute per IP address
- Wait for the rate limit window to reset (check `X-RateLimit-Reset` header)
- Rate limits are per-IP to prevent abuse while allowing normal use

### Manual Image Display
```bash
python3 display_image.py /path/to/image.jpg
```

### Manual Rotation Test
```bash
python3 rotate_image.py
```

## License

MIT License - Feel free to modify and use for your own projects.
