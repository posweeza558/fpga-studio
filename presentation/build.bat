@echo off
cd /d "%~dp0"
echo ===================================================
echo Compiling FPGA Studio Presentation (Nothing Edition)
echo ===================================================
python build_presentation.py
echo.
pause
