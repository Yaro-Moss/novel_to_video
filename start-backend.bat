@echo off
echo ========================================
echo 启动后端服务
echo ========================================

cd /d "%~dp0backend"

echo.
echo [1/2] 检查是否有数据库，没有则初始化...
if not exist "novel_to_video.db" (
    python init_db.py
)

echo.
echo [2/2] 启动 FastAPI 后端...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
