#!/usr/bin/env python3
"""
Simple entry point to run the dashboard
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

if __name__ == "__main__":
    # Change to the project directory to ensure relative paths work
    os.chdir(Path(__file__).parent)

    # Run streamlit
    os.system("streamlit run src/dashboard.py")
