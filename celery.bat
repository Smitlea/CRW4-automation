@echo off
cd /d "%~dp0"
pipenv run celery -A tasks.Celery_app worker -l INFO --pool=solo
pause
