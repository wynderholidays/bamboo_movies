@echo off
echo Starting Movie Booking Application...
echo.

echo Starting Backend Server...
start cmd /k "cd backend && python run.py"

timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start cmd /k "cd frontend && npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
pause