@echo off
cd backend

echo Installing dependencies...
pip install -r requirements.txt

echo Running migrations...
python -m alembic upgrade head

echo Starting Backend...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
