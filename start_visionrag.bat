@echo off
echo ===================================================
echo Starting VisionRAG Pro (Enterprise Document Analyzer)
echo ===================================================

echo.
echo [1/2] Starting FastAPI Backend...
start cmd /k "title VisionRAG Backend && python -m uvicorn main:app --port 8000"

echo.
echo [2/2] Starting React Frontend...
start cmd /k "title VisionRAG Frontend && cd frontend && npm run dev -- --host --port 3000"

echo.
echo Servers are starting in separate windows!
echo Please wait a few seconds, then open your browser to:
echo http://localhost:3000
echo.
pause
