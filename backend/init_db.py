"""
数据库初始化脚本
创建所有数据库表
"""

from app.core.database import Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.api_key import ApiKey

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
