#!/usr/bin/env python3
import sys
import os

# Add the e-paper library to the path
# Check environment variable first, then fall back to current user, then default
epaper_lib = os.environ.get('EPAPER_LIB_PATH')
if not epaper_lib:
    # Use current user's home directory
    current_user = os.environ.get('USER', 'alfon')
    epaper_lib = f'/home/{current_user}/e-Paper/RaspberryPi_JetsonNano/python/lib'

if os.path.exists(epaper_lib):
    sys.path.append(epaper_lib)

import logging
from waveshare_epd import epd5in65f
from PIL import Image
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_image_on_epaper(image_path):
    """
    Display an image on the 5.65" 7-color e-paper display

    Args:
        image_path: Path to the image file to display

    Returns:
        0 on success, 1 on error
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return 1

        logger.info(f"Displaying image: {image_path}")

        # Initialize the display
        epd = epd5in65f.EPD()
        logger.info("Initializing e-paper display...")
        epd.init()

        # Open and prepare the image
        logger.info("Loading image...")
        image = Image.open(image_path)

        # Get display dimensions
        display_width = epd.width   # 600
        display_height = epd.height  # 448

        # Resize image to fit display while maintaining aspect ratio
        logger.info(f"Original image size: {image.size}")
        logger.info(f"Display size: {display_width}x{display_height}")

        # Calculate scaling to fit image within display
        img_width, img_height = image.size
        width_ratio = display_width / img_width
        height_ratio = display_height / img_height
        scale = min(width_ratio, height_ratio)

        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        logger.info(f"Resizing to: {new_width}x{new_height}")
        image = image.resize((new_width, new_height), Image.LANCZOS)

        # Create a white background image at display size
        display_image = Image.new('RGB', (display_width, display_height), (255, 255, 255))

        # Paste the resized image centered on the white background
        offset_x = (display_width - new_width) // 2
        offset_y = (display_height - new_height) // 2
        display_image.paste(image, (offset_x, offset_y))

        # Display the image
        logger.info("Sending image to display...")
        epd.display(epd.getbuffer(display_image))

        # Put display to sleep to save power
        logger.info("Display complete, putting display to sleep...")
        epd.sleep()

        logger.info("Success!")
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        epd5in65f.epdconfig.module_exit(cleanup=True)
        return 1

    except Exception as e:
        logger.error(f"Error displaying image: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: display_image.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    exit_code = display_image_on_epaper(image_path)
    sys.exit(exit_code)
