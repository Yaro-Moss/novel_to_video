
"""
测试项目状态查询 API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.core.security import get_password_hash


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session: Session, test_user: User):
    """创建测试项目"""
    project = Project(
        user_id=test_user.id,
        name="测试项目",
        input_file="test/test.txt",
        status="pending",
        config={}
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_tasks(db_session: Session, test_project: Project):
    """创建测试任务"""
    now = datetime.now(timezone.utc)
    tasks = [
        Task(
            project_id=test_project.id,
            step_name="import",
            status="completed",
            result="文件导入成功",
            created_at=now - timedelta(minutes=5),
            updated_at=now - timedelta(minutes=4)
        ),
        Task(
            project_id=test_project.id,
            step_name="segmentation",
            status="completed",
            result="分段完成",
            created_at=now - timedelta(minutes=4),
            updated_at=now - timedelta(minutes=3)
        ),
        Task(
            project_id=test_project.id,
            step_name="tts",
            status="running",
            created_at=now - timedelta(minutes=3),
            updated_at=now
        ),
    ]
    for task in tasks:
        db_session.add(task)
    db_session.commit()
    for task in tasks:
        db_session.refresh(task)
    return tasks


def test_get_project_status_pending(
    client: TestClient,
    auth_token: str,
    test_project: Project
):
    """测试获取 pending 状态项目的状态"""
    response = client.get(
        f"/api/v1/projects/{test_project.id}/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == test_project.id
    assert data["status"] == "pending"
    assert data["tasks"] == []


def test_get_project_status_not_found(
    client: TestClient,
    auth_token: str
):
    """测试获取不存在的项目状态"""
    response = client.get(
        "/api/v1/projects/99999/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


def test_get_project_status_unauthorized(
    client: TestClient,
    db_session: Session,
    test_project: Project
):
    """测试未授权访问项目状态"""
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("testpassword123"),
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "testpassword123"}
    )
    other_token = login_response.json()["access_token"]
    
    response = client.get(
        f"/api/v1/projects/{test_project.id}/status",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 404


def test_get_project_status_processing(
    client: TestClient,
    auth_token: str,
    db_session: Session,
    test_project: Project,
    test_tasks: list[Task]
):
    """测试获取 processing 状态项目的状态"""
    test_project.status = "processing"
    db_session.commit()

    response = client.get(
        f"/api/v1/projects/{test_project.id}/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert len(data["tasks"]) == 3


def test_get_project_status_failed(
    client: TestClient,
    auth_token: str,
    db_session: Session,
    test_project: Project,
    test_tasks: list[Task]
):
    """测试获取 failed 状态项目的状态"""
    test_project.status = "failed"
    test_tasks[2].status = "failed"
    test_tasks[2].error = "TTS 生成失败"
    db_session.commit()

    response = client.get(
        f"/api/v1/projects/{test_project.id}/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"


def test_get_project_status_completed(
    client: TestClient,
    auth_token: str,
    db_session: Session,
    test_project: Project,
    test_tasks: list[Task]
):
    """测试获取 completed 状态项目的状态"""
    test_project.status = "completed"
    for task in test_tasks:
        task.status = "completed"
    for i in range(3):
        task = Task(
            project_id=test_project.id,
            step_name=f"step_{i}",
            status="completed"
        )
        db_session.add(task)
    db_session.commit()

    response = client.get(
        f"/api/v1/projects/{test_project.id}/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

