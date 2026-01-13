#!/usr/bin/env python3
"""
Quick test script to verify EasyOCR is working with the uploaded screenshot
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ocr_processor import SicalOCRProcessor, EASYOCR_AVAILABLE

def main():
    print("="*70)
    print("SICAL II - EasyOCR Test")
    print("="*70)
    print()

    # Check if EasyOCR is available
    if EASYOCR_AVAILABLE:
        print("✓ EasyOCR is installed and available")
    else:
        print("✗ EasyOCR is NOT available")
        print("  Install with: pip install easyocr")
        return

    print()

    # Find screenshot
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        screenshots_dir = Path("screenshots")
        images = list(screenshots_dir.glob("*.png")) + \
                 list(screenshots_dir.glob("*.jpg"))

        if not images:
            print("No images found in screenshots/ folder")
            print()
            print("Usage: python test_easyocr.py <path-to-image>")
            return

        image_path = images[0]
        print(f"Testing with: {image_path.name}")

    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        return

    print()
    print("-"*70)
    print("Initializing OCR processor with EasyOCR...")
    print("-"*70)

    # Initialize processor (will use EasyOCR by default)
    processor = SicalOCRProcessor(use_easyocr='auto')

    print()
    print("-"*70)
    print("Extracting data...")
    print("-"*70)
    print()

    # Extract data
    data = processor.extract_data(image_path)

    print()
    print("="*70)
    print("RESULTS")
    print("="*70)
    print()

    if data:
        # Show extracted data
        fields_found = 0
        fields_total = 0

        for key, value in data.items():
            if key not in ['timestamp', 'image_file']:
                fields_total += 1
                if value is not None:
                    fields_found += 1
                    print(f"✓ {key:30s}: {value}")
                else:
                    print(f"✗ {key:30s}: Not found")

        print()
        print("-"*70)
        print(f"Summary: {fields_found}/{fields_total} fields extracted successfully")
        print("-"*70)

        if fields_found == 0:
            print()
            print("⚠ No fields were extracted!")
            print()
            print("Possible causes:")
            print("  1. The image quality is too low")
            print("  2. The SICAL II layout is different than expected")
            print("  3. The field names don't match the expected patterns")
            print()
            print("Run the following for more details:")
            print(f"  python test_ocr.py \"{image_path}\"")
        elif fields_found < fields_total:
            print()
            print(f"⚠ Only {fields_found} out of {fields_total} fields were extracted")
            print()
            print("You may need to:")
            print("  1. Improve the screenshot quality")
            print("  2. Check the field patterns in the code")
    else:
        print("✗ No data could be extracted from the image")
        print()
        print("This usually means:")
        print("  - The OCR couldn't read any text from the image")
        print("  - The image file is corrupted or invalid")
        print()
        print("Try running: python debug_preprocessing.py to see the image preprocessing")

    print()
    print("="*70)


if __name__ == "__main__":
    main()
