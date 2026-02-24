#!/bin/bash
echo "===== FEDHEALTH STARTUP ====="
echo ""
echo "Starting Backend Server..."
cd backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!
echo ""
echo "Waiting 3 seconds before starting Frontend..."
sleep 3
echo ""
echo "Starting Frontend Server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo ""
echo "===== SERVERS STARTED ====="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"
wait
