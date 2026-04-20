"""测试后端API功能"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.project import Project
from sqlalchemy.orm import Session

print("=== 后端功能测试 ===\n")

# 1. 测试数据库连接
print("1. 测试数据库连接...")
try:
    db = SessionLocal()
    # 测试查询
    users = db.query(User).all()
    print(f"   ✓ 数据库连接成功！当前有 {len(users)} 个用户")
    db.close()
except Exception as e:
    print(f"   ✗ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()

print("\n2. 检查路由...")
print("   可用的 API 路由:")
for route in app.routes:
    if route.path.startswith("/api/"):
        print(f"   - {route.methods} {route.path}")

print("\n=== 测试完成 ===")
print("\n提示: 如果需要创建测试用户，可以使用注册 API。")
