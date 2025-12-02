@echo off
REM Bunker Game Run Script for Windows

echo 🎮 Starting Гра бункер...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r backend\requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    echo ⚙️  Creating .env file...
    copy .env.example .env
)

REM Run the application
echo.
echo 🚀 Starting server...
echo 🌐 Access the game at: http://localhost:8000
echo.
echo Press Ctrl+C to stop
echo.

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
