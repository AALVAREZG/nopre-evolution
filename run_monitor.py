#!/usr/bin/env python3
"""
Simple entry point to run the SICAL II monitor
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from monitor import start_monitoring

if __name__ == "__main__":
    print("="*60)
    print("SICAL II - Monitor de Capturas de Pantalla")
    print("="*60)
    print()
    print("Este script monitoreará la carpeta 'screenshots/' y procesará")
    print("automáticamente cualquier captura de pantalla que añadas.")
    print()
    print("Las capturas procesadas se moverán a la carpeta 'processed/'")
    print("y los datos se guardarán en la base de datos.")
    print()
    print("Presiona Ctrl+C para detener el monitor.")
    print("="*60)
    print()

    start_monitoring()
