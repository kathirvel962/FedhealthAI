#!/bin/bash
echo "===== FEDHEALTH SETUP ====="
echo ""
echo "Backend Setup..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo ""
echo "Frontend Setup..."
cd ../frontend
npm install
echo ""
echo "===== SETUP COMPLETE ====="
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && python manage.py runserver"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "Make sure MongoDB is running on localhost:27017"
