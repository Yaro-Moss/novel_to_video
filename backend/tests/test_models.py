"""
数据模型测试
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import User, Project, Task, ApiKey


@pytest.fixture(scope="function")
def db_session():
    """测试数据库会话 fixture"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_user_model_creation(db_session):
    """测试 User 模型创建"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpass123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashedpass123"
    assert user.created_at is not None


def test_project_model_creation(db_session):
    """测试 Project 模型创建"""
    # 先创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpass123"
    )
    db_session.add(user)
    db_session.commit()

    # 创建项目
    project = Project(
        user_id=user.id,
        name="Test Project",
        input_file="test.txt",
        status="pending",
        config={"tts": {"voice": "zh-CN-XiaoxiaoNeural"}}
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    assert project.id is not None
    assert project.user_id == user.id
    assert project.name == "Test Project"
    assert project.input_file == "test.txt"
    assert project.status == "pending"
    assert project.config == {"tts": {"voice": "zh-CN-XiaoxiaoNeural"}}
    assert project.created_at is not None


def test_task_model_creation(db_session):
    """测试 Task 模型创建"""
    # 创建用户和项目
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpass123")
    db_session.add(user)
    db_session.commit()

    project = Project(user_id=user.id, name="Test", input_file="test.txt")
    db_session.add(project)
    db_session.commit()

    # 创建任务
    task = Task(
        project_id=project.id,
        step_name="tts",
        status="pending",
        celery_task_id="task-123"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.project_id == project.id
    assert task.step_name == "tts"
    assert task.status == "pending"
    assert task.celery_task_id == "task-123"


def test_api_key_model_creation(db_session):
    """测试 ApiKey 模型创建"""
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpass123")
    db_session.add(user)
    db_session.commit()

    api_key = ApiKey(
        user_id=user.id,
        provider="openai",
        encrypted_key="encrypted-key-123"
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert api_key.id is not None
    assert api_key.user_id == user.id
    assert api_key.provider == "openai"
    assert api_key.encrypted_key == "encrypted-key-123"


def test_relationships(db_session):
    """测试模型关系"""
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpass123")
    db_session.add(user)
    db_session.commit()

    # 创建项目
    project = Project(user_id=user.id, name="Test", input_file="test.txt")
    db_session.add(project)
    db_session.commit()

    # 创建 API Key
    api_key = ApiKey(user_id=user.id, provider="openai", encrypted_key="key")
    db_session.add(api_key)
    db_session.commit()

    # 创建任务
    task = Task(project_id=project.id, step_name="tts", status="pending")
    db_session.add(task)
    db_session.commit()

    # 刷新用户
    db_session.refresh(user)
    db_session.refresh(project)

    # 测试关系
    assert len(user.projects) == 1
    assert user.projects[0].id == project.id
    assert len(user.api_keys) == 1
    assert user.api_keys[0].id == api_key.id
    assert len(project.tasks) == 1
    assert project.tasks[0].id == task.id
    assert project.owner.id == user.id
    assert task.project.id == project.id
