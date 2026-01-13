"""
Monitor screenshots folder and process new images automatically
"""

import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

from ocr_processor import SicalOCRProcessor
from database import SicalDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScreenshotHandler(FileSystemEventHandler):
    """Handle new screenshot files"""

    def __init__(self, processor, database, screenshots_dir, processed_dir):
        self.processor = processor
        self.database = database
        self.screenshots_dir = Path(screenshots_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        """Process new files"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process image files
        if file_path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return

        logger.info(f"New file detected: {file_path.name}")

        # Wait a bit to ensure file is fully written
        time.sleep(2)

        # Check if already processed
        if self.database.is_file_processed(file_path.name):
            logger.info(f"File {file_path.name} already processed, skipping")
            return

        # Process the file
        self.process_file(file_path)

    def process_file(self, file_path):
        """Process a single screenshot file"""
        try:
            logger.info(f"Processing {file_path.name}...")

            # Extract data using OCR
            data = self.processor.extract_data(file_path)

            if data:
                # Save to database
                self.database.insert_data(data)

                # Mark as processed
                self.database.mark_file_processed(file_path.name)

                # Move to processed folder
                dest_path = self.processed_dir / file_path.name
                shutil.move(str(file_path), str(dest_path))

                logger.info(f"Successfully processed {file_path.name}")
                logger.info(f"Extracted concept: {data.get('concept')}, "
                           f"Year: {data.get('year')}")
            else:
                logger.warning(f"No data extracted from {file_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")


def process_existing_files(screenshots_dir, processed_dir):
    """Process any existing files in the screenshots directory"""
    screenshots_path = Path(screenshots_dir)
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    processor = SicalOCRProcessor()
    database = SicalDatabase()

    image_files = list(screenshots_path.glob('*.png')) + \
                  list(screenshots_path.glob('*.jpg')) + \
                  list(screenshots_path.glob('*.jpeg'))

    if image_files:
        logger.info(f"Found {len(image_files)} existing files to process")

        for file_path in image_files:
            # Check if already processed
            if database.is_file_processed(file_path.name):
                logger.info(f"Skipping already processed file: {file_path.name}")
                continue

            try:
                logger.info(f"Processing {file_path.name}...")

                # Extract data
                data = processor.extract_data(file_path)

                if data:
                    # Save to database
                    database.insert_data(data)

                    # Mark as processed
                    database.mark_file_processed(file_path.name)

                    # Move to processed folder
                    dest_path = processed_path / file_path.name
                    shutil.move(str(file_path), str(dest_path))

                    logger.info(f"Successfully processed {file_path.name}")
                else:
                    logger.warning(f"No data extracted from {file_path.name}")

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
    else:
        logger.info("No existing files to process")


def start_monitoring(screenshots_dir='screenshots', processed_dir='processed'):
    """Start monitoring the screenshots directory"""
    screenshots_path = Path(screenshots_dir)
    screenshots_path.mkdir(parents=True, exist_ok=True)

    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing SICAL II Screenshot Monitor...")

    # Initialize processor and database
    processor = SicalOCRProcessor()
    database = SicalDatabase()

    # Process any existing files first
    logger.info("Processing existing files...")
    process_existing_files(screenshots_dir, processed_dir)

    # Set up file system monitoring
    event_handler = ScreenshotHandler(
        processor, database, screenshots_path, processed_path
    )
    observer = Observer()
    observer.schedule(event_handler, str(screenshots_path), recursive=False)

    logger.info(f"Starting file system monitor on {screenshots_path}")
    logger.info("Waiting for new screenshots...")
    logger.info("Press Ctrl+C to stop")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping monitor...")
        observer.stop()

    observer.join()
    logger.info("Monitor stopped")


if __name__ == "__main__":
    start_monitoring()
