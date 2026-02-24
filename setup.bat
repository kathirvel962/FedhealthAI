@echo off
echo ===== FEDHEALTH SETUP =====
echo.
echo Backend Setup...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo Frontend Setup...
cd ..\frontend
call npm install
echo.
echo ===== SETUP COMPLETE =====
echo.
echo To start the application:
echo 1. Backend: cd backend && venv\Scripts\activate.bat && python manage.py runserver
echo 2. Frontend: cd frontend && npm run dev
echo.
echo Make sure MongoDB is running on localhost:27017
