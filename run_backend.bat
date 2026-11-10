@echo off
title SafeSpace AI Therapist - Backend Server
echo Starting FastAPI Backend on http://localhost:8000 ...
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
pause

