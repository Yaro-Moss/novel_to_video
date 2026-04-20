"""
项目管理 API 测试
"""
import io
from fastapi.testclient import TestClient

from app.core.config import settings


def get_auth_token(client: TestClient):
    """Helper function to register and get auth token"""
    client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    login_response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    return login_response.json()["access_token"]


def test_create_project_success(client: TestClient):
    """Test successful project creation"""
    token = get_auth_token(client)
    file_content = "This is test content."
    file = io.BytesIO(file_content.encode("utf-8"))
    
    response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.txt", file, "text/plain")},
        data={"name": "My Test Project"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Test Project"
    assert data["status"] == "pending"
    assert "id" in data
    assert "input_file" in data


def test_create_project_invalid_file_type(client: TestClient):
    """Test uploading invalid file type"""
    token = get_auth_token(client)
    file = io.BytesIO(b"test content")
    
    response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.jpg", file, "image/jpeg")},
        data={"name": "Test Project"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "txt" in response.json()["detail"].lower()


def test_create_project_unauthorized(client: TestClient):
    """Test creating project without auth"""
    file = io.BytesIO(b"test content")
    
    response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.txt", file, "text/plain")},
        data={"name": "Test Project"}
    )
    
    assert response.status_code == 401


def test_list_projects_success(client: TestClient):
    """Test getting project list"""
    token = get_auth_token(client)
    for i in range(3):
        file = io.BytesIO(f"content{i}".encode("utf-8"))
        client.post(
            f"{settings.API_PREFIX}/projects/",
            files={"file": (f"test{i}.txt", file, "text/plain")},
            data={"name": f"Project{i}"},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    response = client.get(f"{settings.API_PREFIX}/projects/", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_list_projects_pagination(client: TestClient):
    """Test pagination"""
    token = get_auth_token(client)
    for i in range(5):
        file = io.BytesIO(f"content{i}".encode("utf-8"))
        client.post(
            f"{settings.API_PREFIX}/projects/",
            files={"file": (f"test{i}.txt", file, "text/plain")},
            data={"name": f"Project{i}"},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    response = client.get(f"{settings.API_PREFIX}/projects/?page=1&page_size=2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_list_projects_status_filter(client: TestClient):
    """Test status filter"""
    token = get_auth_token(client)
    for i in range(2):
        file = io.BytesIO(f"content{i}".encode("utf-8"))
        client.post(
            f"{settings.API_PREFIX}/projects/",
            files={"file": (f"test{i}.txt", file, "text/plain")},
            data={"name": f"Project{i}"},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    response = client.get(f"{settings.API_PREFIX}/projects/?status=pending", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_get_project_success(client: TestClient):
    """Test getting project detail"""
    token = get_auth_token(client)
    file = io.BytesIO(b"test content")
    create_response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.txt", file, "text/plain")},
        data={"name": "Detail Test Project"},
        headers={"Authorization": f"Bearer {token}"}
    )
    project_id = create_response.json()["id"]
    
    response = client.get(f"{settings.API_PREFIX}/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Detail Test Project"


def test_get_project_not_found(client: TestClient):
    """Test getting non-existent project"""
    token = get_auth_token(client)
    response = client.get(f"{settings.API_PREFIX}/projects/99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_delete_project_success(client: TestClient):
    """Test deleting project"""
    token = get_auth_token(client)
    file = io.BytesIO(b"test content")
    create_response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.txt", file, "text/plain")},
        data={"name": "To Delete Project"},
        headers={"Authorization": f"Bearer {token}"}
    )
    project_id = create_response.json()["id"]
    
    response = client.delete(f"{settings.API_PREFIX}/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    
    get_response = client.get(f"{settings.API_PREFIX}/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 404


def test_update_project_success(client: TestClient):
    """Test updating project"""
    token = get_auth_token(client)
    file = io.BytesIO(b"test content")
    create_response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.txt", file, "text/plain")},
        data={"name": "Original Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    project_id = create_response.json()["id"]
    
    response = client.patch(
        f"{settings.API_PREFIX}/projects/{project_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"


def test_update_project_config(client: TestClient):
    """Test updating project config"""
    token = get_auth_token(client)
    file = io.BytesIO(b"test content")
    create_response = client.post(
        f"{settings.API_PREFIX}/projects/",
        files={"file": ("test.txt", file, "text/plain")},
        data={"name": "Config Test Project"},
        headers={"Authorization": f"Bearer {token}"}
    )
    project_id = create_response.json()["id"]
    
    response = client.patch(
        f"{settings.API_PREFIX}/projects/{project_id}",
        json={
            "config": {
                "tts": {"voice": "zh-CN-XiaoxiaoNeural"},
                "image": {"style": "anime"}
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["config"]["tts"]["voice"] == "zh-CN-XiaoxiaoNeural"
