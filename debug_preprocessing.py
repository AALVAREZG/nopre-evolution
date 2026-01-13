#!/usr/bin/env python3
"""
Debug script to visualize image preprocessing steps
Saves preprocessed images to help debug OCR issues
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ocr_processor import SicalOCRProcessor


def save_preprocessing_stages(image_path, output_dir='debug_images'):
    """Save all preprocessing stages for visual inspection"""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    processor = SicalOCRProcessor()

    # Load original image
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"Error: Could not load {image_path}")
        return

    image_name = Path(image_path).stem

    # Save original
    cv2.imwrite(str(output_path / f"{image_name}_0_original.png"), img)
    print(f"Saved: {image_name}_0_original.png")

    # Save grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(str(output_path / f"{image_name}_1_grayscale.png"), gray)
    print(f"Saved: {image_name}_1_grayscale.png")

    # Method 1: Basic preprocessing
    try:
        processed = processor.preprocess_image(image_path, method='basic')
        cv2.imwrite(str(output_path / f"{image_name}_2_basic.png"), processed)
        print(f"Saved: {image_name}_2_basic.png")
    except Exception as e:
        print(f"Basic preprocessing failed: {e}")

    # Method 2: Advanced preprocessing
    try:
        processed = processor.preprocess_image(image_path, method='advanced')
        cv2.imwrite(str(output_path / f"{image_name}_3_advanced.png"), processed)
        print(f"Saved: {image_name}_3_advanced.png")
    except Exception as e:
        print(f"Advanced preprocessing failed: {e}")

    # Method 3: Contrast preprocessing
    try:
        processed = processor.preprocess_image(image_path, method='contrast')
        cv2.imwrite(str(output_path / f"{image_name}_4_contrast.png"), processed)
        print(f"Saved: {image_name}_4_contrast.png")
    except Exception as e:
        print(f"Contrast preprocessing failed: {e}")

    # Additional: High contrast version
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        alpha = 2.0  # Very high contrast
        beta = 0
        high_contrast = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        _, binary = cv2.threshold(high_contrast, 180, 255, cv2.THRESH_BINARY)
        cv2.imwrite(str(output_path / f"{image_name}_5_high_contrast.png"), binary)
        print(f"Saved: {image_name}_5_high_contrast.png")
    except Exception as e:
        print(f"High contrast failed: {e}")

    # Additional: Inverted
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = cv2.bitwise_not(gray)
        cv2.imwrite(str(output_path / f"{image_name}_6_inverted.png"), inverted)
        print(f"Saved: {image_name}_6_inverted.png")
    except Exception as e:
        print(f"Inverted failed: {e}")

    print()
    print(f"All preprocessed images saved to: {output_path}/")
    print()
    print("Review these images to see which preprocessing method")
    print("produces the clearest text for OCR.")


if __name__ == "__main__":
    print("="*60)
    print("SICAL II - Image Preprocessing Debugger")
    print("="*60)
    print()

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Look for any image
        screenshots_dir = Path("screenshots")
        processed_dir = Path("processed")

        images = list(screenshots_dir.glob("*.png")) + \
                 list(screenshots_dir.glob("*.jpg")) + \
                 list(processed_dir.glob("*.png"))

        if images:
            image_path = images[0]
            print(f"No image specified, using: {image_path}")
            print()
        else:
            print("Usage: python debug_preprocessing.py <image_path>")
            print()
            print("Or place a screenshot in the screenshots/ folder")
            sys.exit(1)

    save_preprocessing_stages(image_path)
