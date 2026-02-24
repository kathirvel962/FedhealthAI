@echo off
echo ===== FEDHEALTH STARTUP =====
echo.
echo Starting Backend Server...
start cmd /k "cd backend && venv\Scripts\activate.bat && python manage.py runserver"
echo.
echo Waiting 3 seconds before starting Frontend...
timeout /t 3
echo.
echo Starting Frontend Server...
start cmd /k "cd frontend && npm run dev"
echo.
echo ===== SERVERS STARTED =====
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
