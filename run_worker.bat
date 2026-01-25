@echo off
cd backend

echo Starting Celery Worker...
python -m celery -A app.worker.celery_app worker --loglevel=info --pool=solo
