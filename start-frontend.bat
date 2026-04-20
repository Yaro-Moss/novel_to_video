@echo off
echo ========================================
echo 启动前端服务
echo ========================================

cd /d "%~dp0frontend"

echo.
echo 检查是否安装依赖...
if not exist "node_modules" (
    echo 首次运行，安装依赖...
    npm install
)

echo.
echo 启动 Vite 开发服务器...
npm run dev
