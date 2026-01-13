"""
Database management for SICAL II data tracking
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SicalDatabase:
    """Manage SQLite database for tracking budget applications"""

    def __init__(self, db_path='data/sical_tracking.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create main data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budget_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    image_file TEXT NOT NULL,
                    year INTEGER,
                    concept TEXT,
                    concept_description TEXT,
                    saldo_inicial_deudor REAL,
                    saldo_inicial_acreedor REAL,
                    total_haber REAL,
                    total_debe REAL,
                    propuestas_mp REAL,
                    saldo_pendiente_acreedor REAL,
                    saldo_pendiente_deudor REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_concept_timestamp
                ON budget_tracking(concept, timestamp)
            ''')

            # Create processed files tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def is_file_processed(self, filename):
        """Check if a file has already been processed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM processed_files WHERE filename = ?',
                (filename,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def mark_file_processed(self, filename):
        """Mark a file as processed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO processed_files (filename) VALUES (?)',
                    (filename,)
                )
                conn.commit()
                logger.info(f"Marked {filename} as processed")
            except sqlite3.IntegrityError:
                logger.warning(f"File {filename} already marked as processed")

    def insert_data(self, data):
        """Insert extracted data into database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO budget_tracking (
                    timestamp, image_file, year, concept, concept_description,
                    saldo_inicial_deudor, saldo_inicial_acreedor,
                    total_haber, total_debe, propuestas_mp,
                    saldo_pendiente_acreedor, saldo_pendiente_deudor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('timestamp'),
                data.get('image_file'),
                data.get('year'),
                data.get('concept'),
                data.get('concept_description'),
                data.get('saldo_inicial_deudor'),
                data.get('saldo_inicial_acreedor'),
                data.get('total_haber'),
                data.get('total_debe'),
                data.get('propuestas_mp'),
                data.get('saldo_pendiente_acreedor'),
                data.get('saldo_pendiente_deudor')
            ))

            conn.commit()
            logger.info(f"Data inserted for concept {data.get('concept')}")

    def get_concept_history(self, concept):
        """Get all records for a specific concept"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM budget_tracking
                WHERE concept = ?
                ORDER BY timestamp
            ''', (concept,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_concepts(self):
        """Get list of all tracked concepts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT concept, concept_description
                FROM budget_tracking
                WHERE concept IS NOT NULL
                ORDER BY concept
            ''')
            return cursor.fetchall()

    def get_latest_data(self, concept=None):
        """Get the most recent data for a concept or all concepts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if concept:
                cursor.execute('''
                    SELECT * FROM budget_tracking
                    WHERE concept = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (concept,))
            else:
                cursor.execute('''
                    SELECT * FROM budget_tracking
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''')

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_data(self):
        """Get all tracking data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM budget_tracking
                ORDER BY concept, timestamp
            ''')

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def export_to_csv(self, output_path='data/export.csv'):
        """Export data to CSV file"""
        import pandas as pd

        data = self.get_all_data()
        if data:
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            logger.info(f"Data exported to {output_path}")
            return output_path
        return None


if __name__ == "__main__":
    # Test database
    db = SicalDatabase()

    # Test data
    test_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'image_file': 'test.png',
        'year': 2025,
        'concept': '30012',
        'concept_description': 'INGRESOS EN CUENTAS OPERATIVAS PTES. APLICACION',
        'saldo_inicial_deudor': 0.0,
        'saldo_inicial_acreedor': 2131793.20,
        'total_haber': 880033.27,
        'total_debe': 632581.53,
        'propuestas_mp': 12742.79,
        'saldo_pendiente_acreedor': 2318244.94,
        'saldo_pendiente_deudor': 0.0
    }

    db.insert_data(test_data)
    print("\nAll concepts:")
    print(db.get_all_concepts())

    print("\nHistory for concept 30012:")
    history = db.get_concept_history('30012')
    for record in history:
        print(record)
