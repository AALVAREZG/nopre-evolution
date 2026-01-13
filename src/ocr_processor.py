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
    """Process SICAL II screenshots to extract budget data with enhanced OCR"""

    def __init__(self, use_enhanced=True):
        # Multiple Tesseract configurations to try
        self.tesseract_configs = [
            r'--oem 3 --psm 6 -l spa',
            r'--oem 3 --psm 4 -l spa',
            r'--oem 3 --psm 11 -l spa',
            r'--oem 3 --psm 3 -l spa+eng',
        ]
        self.use_enhanced = use_enhanced

    def preprocess_image(self, image_path, method='advanced'):
        """Preprocess image for better OCR results"""
        # Read image
        img = cv2.imread(str(image_path))

        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        if method == 'basic':
            # Basic preprocessing
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            gray = cv2.medianBlur(gray, 3)
            return gray

        elif method == 'advanced':
            # Advanced preprocessing with contrast enhancement
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply CLAHE for contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)

            # Denoise
            gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

            # Adaptive threshold
            gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 11, 2)
            return gray

        elif method == 'contrast':
            # Focus on text with high contrast
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Increase contrast
            alpha = 1.8  # Contrast control
            beta = 10    # Brightness control
            gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

            # Binary threshold
            _, gray = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

            # Clean up noise
            kernel = np.ones((2,2), np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            return gray

        else:
            # Default
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return gray

    def extract_text(self, image_path):
        """Extract all text from image using multiple methods"""
        try:
            best_text = ""
            best_length = 0

            # Try multiple preprocessing methods
            for method in ['advanced', 'contrast', 'basic']:
                try:
                    processed_img = self.preprocess_image(image_path, method=method)
                    pil_img = Image.fromarray(processed_img)

                    # Try each config
                    for config in self.tesseract_configs:
                        text = pytesseract.image_to_string(pil_img, config=config)

                        # Keep the result with most text
                        if len(text) > best_length:
                            best_text = text
                            best_length = len(text)
                            logger.debug(f"Better result with method={method}, config={config}")

                except Exception as e:
                    logger.debug(f"Method {method} failed: {e}")
                    continue

            return best_text

        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return ""

    def clean_number(self, text):
        """Clean and convert Spanish number format to float"""
        if not text:
            return None

        text = str(text).strip()

        # Remove any non-numeric characters except . , -
        text = re.sub(r'[^\d.,-]', '', text)

        if not text or text in ['-', '.', ',', '']:
            return None

        # Spanish format: 2.131.793,20 -> 2131793.20
        # Count dots and commas to determine format
        dots = text.count('.')
        commas = text.count(',')

        if dots > 0 and commas > 0:
            # Has both - assume Spanish format: thousands with dot, decimal with comma
            text = text.replace('.', '')
            text = text.replace(',', '.')
        elif commas == 1 and dots == 0:
            # Only comma - decimal separator
            text = text.replace(',', '.')
        elif dots > 1:
            # Multiple dots - thousands separators
            text = text.replace('.', '')
        elif dots == 1 and commas == 0:
            # Single dot - could be decimal or thousands
            # If it has 3 digits after dot, it's probably thousands
            parts = text.split('.')
            if len(parts) == 2 and len(parts[1]) == 3:
                # Likely thousands separator
                text = text.replace('.', '')

        try:
            value = float(text)
            # Sanity check - values should be reasonable
            if abs(value) > 1e15:  # Too large
                return None
            return value
        except (ValueError, AttributeError):
            return None

    def extract_field_value(self, text, field_name, next_field=None):
        """Extract numeric value following a field name with improved patterns"""
        # Handle OCR variations (ñ might be read as fi, n, etc.)
        field_variants = [field_name]

        if 'ñ' in field_name:
            field_variants.append(field_name.replace('ñ', 'n'))
            field_variants.append(field_name.replace('ñ', 'fi'))

        all_patterns = []

        for variant in field_variants:
            patterns = [
                # Pattern 1: Field name followed by number on same or next line
                rf'{variant}\s*[:\s]+([0-9.,]+)',
                # Pattern 2: Field name, optional colon, whitespace, then number
                rf'{variant}\s*:?\s*([0-9.,]+)',
                # Pattern 3: Field name in a box, number nearby (within 50 chars)
                rf'{variant}.{{0,50}}?([0-9.,]+)',
                # Pattern 4: More lenient - field name then any number within 100 chars
                rf'{variant}.{{0,100}}?([0-9]{{1,3}}(?:[.,][0-9]{{3}})*(?:[.,][0-9]{{2}})?)',
            ]
            all_patterns.extend(patterns)

        for pattern in all_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)

            for match in matches:
                # Try all captured groups
                for i in range(1, len(match.groups()) + 1):
                    try:
                        number_str = match.group(i)
                        value = self.clean_number(number_str)
                        if value is not None and value != 0:
                            return value
                    except:
                        continue

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

    def find_all_numbers(self, text):
        """Find all numbers in text"""
        pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)'
        matches = re.findall(pattern, text)
        numbers = []
        for match in matches:
            num = self.clean_number(match)
            if num is not None:
                numbers.append(num)
        return numbers

    def extract_data(self, image_path):
        """Extract all relevant data from screenshot with enhanced methods"""
        logger.info(f"Processing: {image_path}")

        # Extract text
        text = self.extract_text(image_path)

        if not text:
            logger.warning(f"No text extracted from {image_path}")
            return None

        logger.debug(f"Extracted text length: {len(text)} characters")
        logger.debug(f"First 500 chars: {text[:500]}")

        # Extract year (Año) - try multiple patterns
        year = None
        year_patterns = [
            r'A[ñn]o[:\s]+(\d{4})',
            r'Afio[:\s]+(\d{4})',  # OCR might confuse ñ
            r'\b(20[0-9]{2})\b',   # Just find a year
        ]

        for pattern in year_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 2000 <= year <= 2100:
                    break

        # Extract concept code (Concepto) - try multiple patterns
        concept = None
        concept_patterns = [
            r'Concepto[:\s]+(\d{5})',
            r'Concepto[:\s]+(\d{4,6})',
            r'(?:Concepto|concepto)[:\s]+(\d+)',
        ]

        for pattern in concept_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                concept = match.group(1)
                break

        # If not found, look for 5-digit numbers in first lines
        if not concept:
            first_lines = '\n'.join(text.split('\n')[:10])
            five_digit = re.findall(r'\b(\d{5})\b', first_lines)
            if five_digit:
                concept = five_digit[0]

        # Extract concept description
        concept_desc = None
        desc_patterns = [
            r'INGRESOS[^\n]*',
            r'INGRESOS.*?(?=\n|$)',
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                concept_desc = match.group(0).strip()
                break

        # Extract Saldo Inicial (Deudor/Acreedor)
        saldo_inicial_deudor = None
        saldo_inicial_acreedor = None

        # Try to find Deudor and Acreedor values
        deudor_patterns = [
            r'Deudor[:\s]+([0-9.,]+)',
            r'Saldo\s+Inicial[:\s]+Deudor[:\s]+([0-9.,]+)',
        ]

        acreedor_patterns = [
            r'Acreedor[:\s]+([0-9.,]+)',
            r'Saldo\s+Inicial[:\s]+Acreedor[:\s]+([0-9.,]+)',
        ]

        for pattern in deudor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                saldo_inicial_deudor = self.clean_number(matches[0])
                if saldo_inicial_deudor is not None:
                    break

        for pattern in acreedor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                saldo_inicial_acreedor = self.clean_number(matches[0])
                if saldo_inicial_acreedor is not None:
                    break

        # Extract movements
        total_haber = self.extract_field_value(text, 'Total Haber')
        if total_haber is None:
            total_haber = self.extract_field_value(text, 'Haber')

        total_debe = self.extract_field_value(text, 'Total Debe')
        if total_debe is None:
            total_debe = self.extract_field_value(text, 'Debe')

        # Extract Propuestas
        propuestas_mp = self.extract_field_value(text, 'Propuestas de M/P')
        if propuestas_mp is None:
            propuestas_mp = self.extract_field_value(text, 'Propuestas de M')
        if propuestas_mp is None:
            propuestas_mp = self.extract_field_value(text, 'Propuestas')

        # Extract pending balances
        saldo_pend_acreedor = self.extract_field_value(text, 'Saldo Pendiente Acreedor')
        if saldo_pend_acreedor is None:
            saldo_pend_acreedor = self.extract_field_value(text, 'Pendiente Acreedor')

        saldo_pend_deudor = self.extract_field_value(text, 'Saldo Pendiente Deudor')
        if saldo_pend_deudor is None:
            saldo_pend_deudor = self.extract_field_value(text, 'Pendiente Deudor')

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

        # Log what was found
        found_fields = [k for k, v in data.items() if v is not None and k not in ['timestamp', 'image_file']]
        logger.info(f"Found {len(found_fields)} fields: {', '.join(found_fields)}")
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
