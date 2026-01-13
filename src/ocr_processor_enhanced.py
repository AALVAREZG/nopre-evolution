"""
Enhanced OCR Processor for SICAL II Screenshots
Uses multiple techniques for better extraction accuracy
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


class SicalOCRProcessorEnhanced:
    """Enhanced processor with multiple OCR strategies"""

    def __init__(self):
        # Multiple Tesseract configurations to try
        self.tesseract_configs = [
            r'--oem 3 --psm 6 -l spa',  # Standard
            r'--oem 3 --psm 4 -l spa',  # Single column
            r'--oem 3 --psm 11 -l spa', # Sparse text
            r'--oem 3 --psm 6 -l spa+eng',  # Spanish + English
        ]

    def preprocess_image_v1(self, img):
        """Basic preprocessing"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        gray = cv2.medianBlur(gray, 3)
        return gray

    def preprocess_image_v2(self, img):
        """Advanced preprocessing with contrast enhancement"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Threshold
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        return gray

    def preprocess_image_v3(self, img):
        """Preprocessing focusing on text areas"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Increase contrast
        alpha = 1.5  # Contrast control
        beta = 0     # Brightness control
        gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

        # Binary threshold
        _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Remove noise
        kernel = np.ones((2,2), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

        return gray

    def extract_text_multimethod(self, image_path):
        """Try multiple preprocessing methods and return all results"""
        img = cv2.imread(str(image_path))
        if img is None:
            return []

        results = []

        # Try different preprocessing methods
        preprocessors = [
            self.preprocess_image_v1,
            self.preprocess_image_v2,
            self.preprocess_image_v3
        ]

        for i, preprocessor in enumerate(preprocessors):
            try:
                processed = preprocessor(img)
                pil_img = Image.fromarray(processed)

                # Try each Tesseract config
                for j, config in enumerate(self.tesseract_configs):
                    text = pytesseract.image_to_string(pil_img, config=config)
                    if text.strip():
                        results.append({
                            'method': f'preprocess_v{i+1}_config_{j+1}',
                            'text': text
                        })
            except Exception as e:
                logger.debug(f"Method {i+1} failed: {e}")
                continue

        return results

    def extract_text_from_regions(self, image_path):
        """Extract text from specific regions of the image"""
        img = cv2.imread(str(image_path))
        if img is None:
            return {}

        height, width = img.shape[:2]

        # Define regions based on typical SICAL II layout (proportional)
        # These are approximate regions - may need adjustment
        regions = {
            'header': (0, int(height * 0.15), 0, width),  # Top 15%
            'left_panel': (int(height * 0.15), int(height * 0.65), 0, int(width * 0.55)),
            'right_panel': (int(height * 0.15), int(height * 0.65), int(width * 0.55), width),
            'bottom': (int(height * 0.65), height, 0, width)
        }

        extracted = {}

        for region_name, (y1, y2, x1, x2) in regions.items():
            try:
                roi = img[y1:y2, x1:x2]

                # Preprocess ROI
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

                # OCR on ROI
                pil_roi = Image.fromarray(gray)
                text = pytesseract.image_to_string(pil_roi, config=r'--oem 3 --psm 6 -l spa')

                extracted[region_name] = text

            except Exception as e:
                logger.debug(f"Region {region_name} failed: {e}")
                extracted[region_name] = ""

        return extracted

    def clean_number(self, text):
        """Clean and convert Spanish number format to float"""
        if not text:
            return None

        text = str(text).strip()

        # Remove any non-numeric characters except . , -
        text = re.sub(r'[^\d.,-]', '', text)

        if not text or text in ['-', '.', ',']:
            return None

        # Spanish format: 2.131.793,20 -> 2131793.20
        # Count dots and commas to determine format
        dots = text.count('.')
        commas = text.count(',')

        if dots > 0 and commas > 0:
            # Has both - assume Spanish format
            text = text.replace('.', '')
            text = text.replace(',', '.')
        elif commas == 1 and dots == 0:
            # Only comma - decimal separator
            text = text.replace(',', '.')
        elif dots > 1:
            # Multiple dots - thousands separators
            text = text.replace('.', '')

        try:
            return float(text)
        except (ValueError, AttributeError):
            return None

    def extract_field_aggressive(self, all_texts, field_patterns, next_patterns=None):
        """
        Aggressively search for field values across all text extractions
        """
        # Combine all extracted texts
        combined_text = "\n".join([r['text'] for r in all_texts if 'text' in r])

        # Try each pattern
        for pattern in field_patterns:
            # Search in combined text
            matches = re.finditer(pattern, combined_text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                # Extract all groups and try to find a number
                for i in range(1, len(match.groups()) + 1):
                    try:
                        value = self.clean_number(match.group(i))
                        if value is not None:
                            return value
                    except:
                        continue

        return None

    def extract_year(self, texts):
        """Extract year (Año)"""
        patterns = [
            r'Año[:\s]+(\d{4})',
            r'Afio[:\s]+(\d{4})',  # OCR might confuse ñ with fi
            r'A[ñn]o[:\s]+(\d{4})',
            r'(?:^|\s)(\d{4})(?:\s|$)',  # Just a 4-digit year
        ]

        result = self.extract_field_aggressive(texts, patterns)
        if result and 2000 <= result <= 2100:
            return int(result)

        # Try to find any 4-digit number that looks like a year
        combined = "\n".join([t.get('text', '') for t in texts])
        year_matches = re.findall(r'\b(20[0-9]{2})\b', combined)
        if year_matches:
            return int(year_matches[0])

        return None

    def extract_concept(self, texts):
        """Extract concept code"""
        patterns = [
            r'Concepto[:\s]+(\d{5})',
            r'Concepto[:\s]+(\d{4,6})',
            r'(?:Concepto|concepto)[:\s]+(\d+)',
        ]

        result = self.extract_field_aggressive(texts, patterns)
        if result:
            return str(int(result))

        # Look for 5-digit numbers in header area
        combined = "\n".join([t.get('text', '') for t in texts[:2]])  # First 2 results
        concept_matches = re.findall(r'\b(\d{5})\b', combined)
        if concept_matches:
            return concept_matches[0]

        return None

    def find_numbers_in_text(self, text):
        """Find all number-like patterns in text"""
        # Pattern for Spanish format numbers
        pattern = r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)'
        matches = re.findall(pattern, text)
        numbers = []
        for match in matches:
            num = self.clean_number(match)
            if num is not None:
                numbers.append(num)
        return numbers

    def extract_from_layout(self, image_path):
        """
        Extract data by understanding the visual layout
        """
        regions = self.extract_text_from_regions(image_path)
        data = {}

        # Header should contain year and concept
        header_text = regions.get('header', '')

        # Extract year from header
        year_match = re.search(r'(\d{4})', header_text)
        if year_match:
            data['year'] = int(year_match.group(1))

        # Extract concept from header
        concept_match = re.search(r'(\d{5})', header_text)
        if concept_match:
            data['concept'] = concept_match.group(1)

        # Left panel has initial balances
        left_text = regions.get('left_panel', '')
        left_numbers = self.find_numbers_in_text(left_text)

        # Right panel has movements
        right_text = regions.get('right_panel', '')
        right_numbers = self.find_numbers_in_text(right_text)

        # Try to match numbers to fields based on position and context
        if 'Saldo Inicial' in left_text or 'saldo inicial' in left_text.lower():
            if len(left_numbers) >= 2:
                data['saldo_inicial_deudor'] = left_numbers[0]
                data['saldo_inicial_acreedor'] = left_numbers[1]

        if 'Total Haber' in right_text or 'total haber' in right_text.lower():
            if len(right_numbers) >= 1:
                data['total_haber'] = right_numbers[0]

        if 'Total Debe' in right_text or 'total debe' in right_text.lower():
            if len(right_numbers) >= 2:
                data['total_debe'] = right_numbers[1]

        return data

    def extract_data(self, image_path):
        """Main extraction method combining all strategies"""
        logger.info(f"Processing with enhanced OCR: {image_path}")

        # Strategy 1: Multiple preprocessing methods
        all_texts = self.extract_text_multimethod(image_path)

        if not all_texts:
            logger.warning(f"No text extracted from {image_path}")
            return None

        # Log best OCR result
        best_result = max(all_texts, key=lambda x: len(x['text']))
        logger.info(f"Best OCR method: {best_result['method']}")
        logger.debug(f"OCR text length: {len(best_result['text'])} chars")

        # Strategy 2: Region-based extraction
        layout_data = self.extract_from_layout(image_path)

        # Initialize data structure
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'image_file': Path(image_path).name,
        }

        # Extract year
        year = self.extract_year(all_texts)
        if year is None:
            year = layout_data.get('year')
        data['year'] = year

        # Extract concept
        concept = self.extract_concept(all_texts)
        if concept is None:
            concept = layout_data.get('concept')
        data['concept'] = concept

        # Extract description
        combined_text = "\n".join([t['text'] for t in all_texts])
        desc_match = re.search(r'INGRESOS.*?(?:\n|$)', combined_text, re.IGNORECASE)
        data['concept_description'] = desc_match.group(0).strip() if desc_match else None

        # Extract numbers with multiple strategies
        # Define field patterns
        fields = {
            'saldo_inicial_deudor': [
                r'Deudor[:\s]+([0-9.,]+)',
                r'Saldo\s+Inicial[:\s]+Deudor[:\s]+([0-9.,]+)',
            ],
            'saldo_inicial_acreedor': [
                r'Acreedor[:\s]+([0-9.,]+)',
                r'Saldo\s+Inicial[:\s]+Acreedor[:\s]+([0-9.,]+)',
            ],
            'total_haber': [
                r'Total\s+Haber[:\s]+([0-9.,]+)',
                r'Haber[:\s]+([0-9.,]+)',
            ],
            'total_debe': [
                r'Total\s+Debe[:\s]+([0-9.,]+)',
                r'Debe[:\s]+([0-9.,]+)',
            ],
            'propuestas_mp': [
                r'Propuestas\s+de\s+M[/\\]P[:\s]+([0-9.,]+)',
                r'Propuestas\s+de\s+M[:\s]+([0-9.,]+)',
            ],
            'saldo_pendiente_acreedor': [
                r'Saldo\s+Pendiente\s+Acreedor[:\s]+([0-9.,]+)',
                r'Pendiente\s+Acreedor[:\s]+([0-9.,]+)',
            ],
            'saldo_pendiente_deudor': [
                r'Saldo\s+Pendiente\s+Deudor[:\s]+([0-9.,]+)',
                r'Pendiente\s+Deudor[:\s]+([0-9.,]+)',
            ],
        }

        for field, patterns in fields.items():
            value = self.extract_field_aggressive(all_texts, patterns)
            if value is None:
                value = layout_data.get(field)
            data[field] = value

        logger.info(f"Extracted data: {data}")
        return data


if __name__ == "__main__":
    # Test the enhanced processor
    processor = SicalOCRProcessorEnhanced()

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
        else:
            print("No data extracted")
