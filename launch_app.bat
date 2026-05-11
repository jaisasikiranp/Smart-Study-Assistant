@echo off
set PYTHON_EXE=venv\Scripts\python.exe
if not exist %PYTHON_EXE% set PYTHON_EXE=python

echo Starting Student Smart Planner Desktop Assistant...

:: Ensure no old instances are running
taskkill /f /im python.exe /t 2>nul
timeout /t 2

echo Starting Backend...
start /b %PYTHON_EXE% backend/app.py
timeout /t 5

echo Starting Analytics Dashboard...
start /b %PYTHON_EXE% tracking/dashboard.py
timeout /t 3

echo Starting Floating Voice Assistant...
%PYTHON_EXE% desktop_assistant.py

pause
