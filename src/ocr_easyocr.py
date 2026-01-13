"""
Alternative OCR processor using EasyOCR
EasyOCR is often more accurate for complex UI screenshots
"""

import re
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available. Install with: pip install easyocr")


class SicalEasyOCRProcessor:
    """Process SICAL II screenshots using EasyOCR"""

    def __init__(self):
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR is not installed. Install with: pip install easyocr")

        logger.info("Initializing EasyOCR (this may take a moment)...")
        self.reader = easyocr.Reader(['es', 'en'], gpu=False)

    def clean_number(self, text):
        """Clean and convert Spanish number format to float"""
        if not text:
            return None

        text = str(text).strip()

        # Remove any non-numeric characters except . , -
        text = re.sub(r'[^\d.,-]', '', text)

        if not text or text in ['-', '.', ',', '']:
            return None

        # Spanish format handling
        dots = text.count('.')
        commas = text.count(',')

        if dots > 0 and commas > 0:
            text = text.replace('.', '')
            text = text.replace(',', '.')
        elif commas == 1 and dots == 0:
            text = text.replace(',', '.')
        elif dots > 1:
            text = text.replace('.', '')

        try:
            value = float(text)
            if abs(value) > 1e15:
                return None
            return value
        except (ValueError, AttributeError):
            return None

    def extract_text(self, image_path):
        """Extract text using EasyOCR"""
        try:
            logger.info(f"Running EasyOCR on {image_path}")

            # Read image
            result = self.reader.readtext(str(image_path))

            # Combine all detected text
            texts = []
            for (bbox, text, prob) in result:
                if prob > 0.3:  # Only include confident detections
                    texts.append(text)

            combined_text = '\n'.join(texts)
            logger.info(f"EasyOCR extracted {len(texts)} text blocks")

            return combined_text

        except Exception as e:
            logger.error(f"Error with EasyOCR: {e}")
            return ""

    def extract_field(self, text, patterns):
        """Extract field value using patterns"""
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                for i in range(1, len(match.groups()) + 1):
                    try:
                        value = self.clean_number(match.group(i))
                        if value is not None:
                            return value
                    except:
                        continue
        return None

    def extract_data(self, image_path):
        """Extract all data from screenshot"""
        logger.info(f"Processing with EasyOCR: {image_path}")

        text = self.extract_text(image_path)

        if not text:
            logger.warning("No text extracted")
            return None

        logger.debug(f"Extracted text:\n{text}")

        # Extract year
        year = None
        year_patterns = [
            r'A[ñn]o[:\s]+(\d{4})',
            r'Afio[:\s]+(\d{4})',
            r'\b(20[0-9]{2})\b',
        ]

        for pattern in year_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 2000 <= year <= 2100:
                    break

        # Extract concept
        concept = None
        concept_patterns = [
            r'Concepto[:\s]+(\d{5})',
            r'Concepto[:\s]+(\d{4,6})',
        ]

        for pattern in concept_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                concept = match.group(1)
                break

        if not concept:
            five_digit = re.findall(r'\b(\d{5})\b', text)
            if five_digit:
                concept = five_digit[0]

        # Extract description
        concept_desc = None
        desc_match = re.search(r'INGRESOS[^\n]*', text, re.IGNORECASE)
        if desc_match:
            concept_desc = desc_match.group(0).strip()

        # Extract numeric fields
        saldo_inicial_deudor = self.extract_field(text, [
            r'Deudor[:\s]+([0-9.,]+)',
            r'Saldo\s+Inicial[:\s]+Deudor[:\s]+([0-9.,]+)',
        ])

        saldo_inicial_acreedor = self.extract_field(text, [
            r'Acreedor[:\s]+([0-9.,]+)',
            r'Saldo\s+Inicial[:\s]+Acreedor[:\s]+([0-9.,]+)',
        ])

        total_haber = self.extract_field(text, [
            r'Total\s+Haber[:\s]+([0-9.,]+)',
            r'Haber[:\s]+([0-9.,]+)',
        ])

        total_debe = self.extract_field(text, [
            r'Total\s+Debe[:\s]+([0-9.,]+)',
            r'Debe[:\s]+([0-9.,]+)',
        ])

        propuestas_mp = self.extract_field(text, [
            r'Propuestas\s+de\s+M[/\\]P[:\s]+([0-9.,]+)',
            r'Propuestas[:\s]+([0-9.,]+)',
        ])

        saldo_pend_acreedor = self.extract_field(text, [
            r'Saldo\s+Pendiente\s+Acreedor[:\s]+([0-9.,]+)',
            r'Pendiente\s+Acreedor[:\s]+([0-9.,]+)',
        ])

        saldo_pend_deudor = self.extract_field(text, [
            r'Saldo\s+Pendiente\s+Deudor[:\s]+([0-9.,]+)',
            r'Pendiente\s+Deudor[:\s]+([0-9.,]+)',
        ])

        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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

        found_fields = [k for k, v in data.items() if v is not None and k not in ['timestamp', 'image_file']]
        logger.info(f"Found {len(found_fields)} fields: {', '.join(found_fields)}")

        return data


if __name__ == "__main__":
    if not EASYOCR_AVAILABLE:
        print("EasyOCR not installed. Install with: pip install easyocr")
        exit(1)

    processor = SicalEasyOCRProcessor()

    # Test with images
    test_images = list(Path("screenshots").glob("*.png"))
    if not test_images:
        test_images = list(Path("processed").glob("*.png"))

    for img in test_images:
        print(f"\n{'='*60}")
        print(f"Testing: {img.name}")
        print('='*60)

        data = processor.extract_data(img)
        if data:
            print("\nExtracted data:")
            for key, value in data.items():
                if value is not None:
                    print(f"  {key:30s}: {value}")
