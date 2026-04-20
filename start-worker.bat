@echo off
echo ========================================
echo 启动 Celery Worker
echo ========================================

cd /d "%~dp0backend"

echo.
echo 注意：请确保 Redis 已启动（默认端口 6379）
echo.

echo 启动 Celery Worker...
python -m celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=1 --pool=solo
