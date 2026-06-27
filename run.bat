@echo off
cd /d "%~dp0"
echo Installing required packages using Python 3.11...
py -3.11 -m pip install -r requirements.txt
echo.
echo Starting VisionRAG Pro...
py -3.11 -m streamlit run app.py
pause
