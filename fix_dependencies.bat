@echo off
REM Script to fix numpy/pandas incompatibility on Windows

echo ========================================
echo Fixing numpy/pandas incompatibility
echo ========================================
echo.

echo Step 1: Uninstalling numpy and pandas...
pip uninstall -y numpy pandas

echo.
echo Step 2: Reinstalling numpy...
pip install numpy==1.26.4

echo.
echo Step 3: Reinstalling pandas...
pip install pandas==2.2.1

echo.
echo Step 4: Verifying installation...
python -c "import numpy; print('numpy version:', numpy.__version__)"
python -c "import pandas; print('pandas version:', pandas.__version__)"

echo.
echo ========================================
echo Fix complete!
echo ========================================
echo.
echo You can now run the monitor:
echo   python run_monitor.py
echo.
pause
