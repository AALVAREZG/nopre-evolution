#!/usr/bin/env python3
"""
Cross-platform script to fix numpy/pandas incompatibility
Run this if you get "ValueError: numpy.dtype size changed" error
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and show output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    print("="*60)
    print("Fixing numpy/pandas incompatibility")
    print("="*60)
    print()

    print("This script will:")
    print("  1. Uninstall numpy and pandas")
    print("  2. Reinstall them in the correct order")
    print("  3. Verify the installation")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    print()
    print("-"*60)
    print("Step 1: Uninstalling numpy and pandas...")
    print("-"*60)

    if not run_command(f"{sys.executable} -m pip uninstall -y numpy pandas"):
        print("Warning: Uninstall had issues, continuing anyway...")

    print()
    print("-"*60)
    print("Step 2: Installing numpy...")
    print("-"*60)

    if not run_command(f"{sys.executable} -m pip install numpy==1.26.4"):
        print("ERROR: Failed to install numpy")
        return

    print()
    print("-"*60)
    print("Step 3: Installing pandas...")
    print("-"*60)

    if not run_command(f"{sys.executable} -m pip install pandas==2.2.1"):
        print("ERROR: Failed to install pandas")
        return

    print()
    print("-"*60)
    print("Step 4: Verifying installation...")
    print("-"*60)

    try:
        import numpy
        import pandas
        print(f"✓ numpy version: {numpy.__version__}")
        print(f"✓ pandas version: {pandas.__version__}")
    except Exception as e:
        print(f"ERROR: Verification failed: {e}")
        return

    print()
    print("="*60)
    print("✓ Fix complete!")
    print("="*60)
    print()
    print("You can now run the monitor:")
    print("  python run_monitor.py")
    print()

if __name__ == "__main__":
    main()
