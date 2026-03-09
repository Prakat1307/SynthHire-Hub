#!/bin/bash

echo "========================================"
echo "SynthHire Platform - Quick Setup Script"
echo "========================================"
echo ""

echo "Step 1: Setting up Backend..."
cd backend

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Step 2: Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit backend/.env and add your GEMINI_API_KEY"
    echo ""
    read -p "Press enter to continue..."
fi

echo ""
echo "Step 3: Initializing database..."
python -m scripts.init_db
python -m scripts.seed_data

echo ""
echo "========================================"
echo "Backend setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Make sure Redis is running (redis-server)"
echo "2. Start auth service: uvicorn auth_service.main:app --reload --port 8001"
echo "3. Start session service: uvicorn session_service.main:app --reload --port 8003"
echo ""
echo "Then setup frontend in another terminal:"
echo "1. cd frontend"
echo "2. npm install"
echo "3. npm run dev"
echo ""
