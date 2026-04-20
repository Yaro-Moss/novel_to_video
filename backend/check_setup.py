
"""
检查完整工作流环境设置
"""
import sys

print("=" * 50)
print("检查完整工作流环境")
print("=" * 50)
print()

# 1. 检查 Python 依赖
print("1. 检查 Python 依赖...")
try:
    import celery
    print("   ✅ Celery:", celery.__version__)
except ImportError:
    print("   ❌ Celery 未安装")

try:
    import redis
    print("   ✅ Redis:", redis.__version__)
except ImportError:
    print("   ❌ Redis 未安装")

try:
    import sqlalchemy
    print("   ✅ SQLAlchemy:", sqlalchemy.__version__)
except ImportError:
    print("   ❌ SQLAlchemy 未安装")

print()

# 2. 检查 Redis 连接
print("2. 检查 Redis 连接...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
    r.ping()
    print("   ✅ Redis 连接成功 (localhost:6379)")
    redis_available = True
except Exception as e:
    print("   ❌ Redis 连接失败:", str(e))
    print("   💡 提示：请启动 Redis 服务（使用 Docker 或 Memurai）")
    redis_available = False

print()

# 3. 检查 .env 配置
print("3. 检查 .env 配置...")
try:
    from app.core.config import settings
    print(f"   ✅ WORKFLOW_MODE: {settings.WORKFLOW_MODE}")
    print(f"   ✅ DATABASE_URL: {settings.DATABASE_URL}")
    print(f"   ✅ CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
    config_ok = True
except Exception as e:
    print("   ❌ 配置加载失败:", str(e))
    config_ok = False

print()
print("=" * 50)
print("总结")
print("=" * 50)

if redis_available and config_ok:
    print("✅ 完整工作流环境已就绪！")
    print()
    print("下一步：")
    print("  1. 保持后端服务运行")
    print("  2. 打开新终端运行：start-worker.bat")
    print("  3. 打开前端页面开始使用")
else:
    print("❌ 需要完成以下配置：")
    if not redis_available:
        print("  ⚠️  缺少：Redis 服务（需要安装并启动）")
    if not config_ok:
        print("  ⚠️  配置问题")
    print()
    print("安装 Redis（Windows）：")
    print("  方式一：Docker（推荐）")
    print("    docker run -d -p 6379:6379 --name redis redis:latest")
    print()
    print("  方式二：Memurai")
    print("    下载：https://www.memurai.com/get-memurai")
