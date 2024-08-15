@echo off
cd /d D:\Systex\CRW4-automation
pipenv run celery -A tasks.Celery_app worker -l INFO --pool=solo
pause
