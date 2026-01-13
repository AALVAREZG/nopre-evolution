#!/usr/bin/env python3
"""
Test script to process a specific screenshot and show detailed results
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ocr_processor import SicalOCRProcessor
import cv2
import numpy as np

def show_image_info(image_path):
    """Show information about the image"""
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"Error: Could not load image {image_path}")
        return

    height, width = img.shape[:2]
    print(f"Image dimensions: {width}x{height}")
    print(f"Image shape: {img.shape}")
    print()

def test_screenshot(image_path):
    """Test OCR on a specific screenshot"""
    print("="*60)
    print("SICAL II - OCR Test")
    print("="*60)
    print()

    if not Path(image_path).exists():
        print(f"Error: Image not found at {image_path}")
        print()
        print("Please place a screenshot in the screenshots/ folder")
        return

    print(f"Processing: {image_path}")
    print()

    # Show image info
    show_image_info(image_path)

    # Test OCR
    processor = SicalOCRProcessor()

    print("Extracting text with OCR...")
    print("-"*60)
    text = processor.extract_text(image_path)
    print("RAW OCR OUTPUT:")
    print(text)
    print("-"*60)
    print()

    print("Extracting structured data...")
    data = processor.extract_data(image_path)

    if data:
        print("EXTRACTED DATA:")
        print("-"*60)
        for key, value in data.items():
            if value is not None:
                print(f"{key:30s}: {value}")
        print("-"*60)
    else:
        print("No data extracted!")

    print()
    print("="*60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Look for any image in screenshots folder
        screenshots_dir = Path("screenshots")
        images = list(screenshots_dir.glob("*.png")) + \
                 list(screenshots_dir.glob("*.jpg")) + \
                 list(screenshots_dir.glob("*.jpeg"))

        if images:
            image_path = images[0]
            print(f"No image specified, using: {image_path}")
            print()
        else:
            print("Usage: python test_ocr.py <image_path>")
            print()
            print("Or place a screenshot in the screenshots/ folder")
            sys.exit(1)

    test_screenshot(image_path)
