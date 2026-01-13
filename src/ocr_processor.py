"""
OCR Processor for SICAL II Screenshots
Extracts budgetary data from application screenshots
"""

import cv2
import pytesseract
from PIL import Image
import re
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SicalOCRProcessor:
    """Process SICAL II screenshots to extract budget data"""

    def __init__(self):
        # Configure pytesseract for Spanish
        self.tesseract_config = r'--oem 3 --psm 6 -l spa'

    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        # Read image
        img = cv2.imread(str(image_path))

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Denoise
        gray = cv2.medianBlur(gray, 3)

        return gray

    def extract_text(self, image_path):
        """Extract all text from image"""
        try:
            # Preprocess
            processed_img = self.preprocess_image(image_path)

            # Convert to PIL Image
            pil_img = Image.fromarray(processed_img)

            # Extract text
            text = pytesseract.image_to_string(pil_img, config=self.tesseract_config)

            return text
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return ""

    def clean_number(self, text):
        """Clean and convert Spanish number format to float"""
        if not text:
            return None

        # Remove whitespace
        text = text.strip()

        # Spanish format: 2.131.793,20 -> 2131793.20
        # Remove dots (thousands separator)
        text = text.replace('.', '')
        # Replace comma with dot (decimal separator)
        text = text.replace(',', '.')

        try:
            return float(text)
        except ValueError:
            return None

    def extract_field_value(self, text, field_name, next_field=None):
        """Extract numeric value following a field name"""
        patterns = [
            # Pattern 1: Field name followed by number on same or next line
            rf'{field_name}\s*[\n\s]*?([\d.,]+)',
            # Pattern 2: Field name in a box, number nearby
            rf'{field_name}.*?([\d.,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                number_str = match.group(1)
                value = self.clean_number(number_str)
                if value is not None:
                    return value

        return None

    def extract_two_column_values(self, text, field_name):
        """Extract deudor/acreedor values that appear in two columns"""
        # Look for the field name followed by two numbers
        pattern = rf'{field_name}\s+([\d.,]+)\s+([\d.,]+)'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            deudor = self.clean_number(match.group(1))
            acreedor = self.clean_number(match.group(2))
            return deudor, acreedor

        return None, None

    def extract_data(self, image_path):
        """Extract all relevant data from screenshot"""
        logger.info(f"Processing: {image_path}")

        # Extract text
        text = self.extract_text(image_path)

        if not text:
            logger.warning(f"No text extracted from {image_path}")
            return None

        # Extract year (Año)
        year_match = re.search(r'Año\s*(\d{4})', text, re.IGNORECASE)
        year = int(year_match.group(1)) if year_match else None

        # Extract concept code (Concepto)
        concept_match = re.search(r'Concepto\s*(\d+)', text, re.IGNORECASE)
        concept = concept_match.group(1) if concept_match else None

        # Extract concept description
        desc_match = re.search(r'INGRESOS EN CUENTAS OPERATIVAS.*', text, re.IGNORECASE)
        concept_desc = desc_match.group(0) if desc_match else None

        # Extract Saldo Inicial (Deudor/Acreedor)
        saldo_inicial_deudor, saldo_inicial_acreedor = self.extract_two_column_values(
            text, 'Saldo Inicial'
        )

        # If two-column extraction failed, try individual extraction
        if saldo_inicial_deudor is None:
            # Try to find "Deudor" and "Acreedor" labels
            deudor_match = re.search(r'Deudor\s+([\d.,]+)', text, re.IGNORECASE)
            acreedor_match = re.search(r'Acreedor\s+([\d.,]+)', text, re.IGNORECASE)

            if deudor_match:
                saldo_inicial_deudor = self.clean_number(deudor_match.group(1))
            if acreedor_match:
                saldo_inicial_acreedor = self.clean_number(acreedor_match.group(1))

        # Extract Total Haber
        total_haber = self.extract_field_value(text, 'Total Haber')

        # Extract Total Debe
        total_debe = self.extract_field_value(text, 'Total Debe')

        # Extract Propuestas de M/P
        propuestas_mp = self.extract_field_value(text, 'Propuestas de M/P')

        # Extract Saldo Pendiente Acreedor
        saldo_pend_acreedor = self.extract_field_value(text, 'Saldo Pendiente Acreedor')

        # Extract Saldo Pendiente Deudor
        saldo_pend_deudor = self.extract_field_value(text, 'Saldo Pendiente Deudor')

        # Extract date from image filename or current date
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data = {
            'timestamp': date_str,
            'image_file': Path(image_path).name,
            'year': year,
            'concept': concept,
            'concept_description': concept_desc,
            'saldo_inicial_deudor': saldo_inicial_deudor,
            'saldo_inicial_acreedor': saldo_inicial_acreedor,
            'total_haber': total_haber,
            'total_debe': total_debe,
            'propuestas_mp': propuestas_mp,
            'saldo_pendiente_acreedor': saldo_pend_acreedor,
            'saldo_pendiente_deudor': saldo_pend_deudor
        }

        logger.info(f"Extracted data: {data}")
        return data

    def extract_with_regions(self, image_path):
        """
        Alternative method: Extract data by analyzing specific regions
        This can be more accurate if screenshots have consistent layout
        """
        img = cv2.imread(str(image_path))
        height, width = img.shape[:2]

        # Define regions of interest (ROI) - these are approximate and may need adjustment
        regions = {
            'year': (80, 140, 50, 80),  # x, width, y, height
            'concept': (200, 100, 140, 30),
            'saldo_inicial_deudor': (230, 100, 230, 25),
            'saldo_inicial_acreedor': (230, 100, 255, 25),
            'total_haber': (575, 120, 235, 25),
            'total_debe': (575, 120, 260, 25),
            'propuestas_mp': (230, 100, 335, 25),
            'saldo_pend_acreedor': (575, 120, 330, 25),
            'saldo_pend_deudor': (575, 120, 355, 25),
        }

        data = {}

        for field, (x, w, y, h) in regions.items():
            # Extract ROI
            roi = img[y:y+h, x:x+w]

            # Convert to grayscale and threshold
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            # OCR on ROI
            text = pytesseract.image_to_string(thresh, config=self.tesseract_config)

            # Clean and convert
            if field in ['year', 'concept']:
                data[field] = text.strip()
            else:
                data[field] = self.clean_number(text)

        return data


if __name__ == "__main__":
    # Test the processor
    processor = SicalOCRProcessor()

    # Test with a sample image
    test_image = Path("screenshots").glob("*.png")
    for img in test_image:
        data = processor.extract_data(img)
        print(f"\nExtracted data from {img.name}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
