"""
用户认证 API 测试
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_register(client: TestClient):
    """测试用户注册"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_username(client: TestClient):
    """测试重复用户名注册"""
    client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "testpassword123"
        }
    )
    
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 400


def test_register_duplicate_email(client: TestClient):
    """测试重复邮箱注册"""
    client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser1",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser2",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 400


def test_login(client: TestClient):
    """测试用户登录"""
    client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client: TestClient):
    """测试错误密码登录"""
    client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """测试不存在的用户登录"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 401


def test_get_current_user(authenticated_client: TestClient):
    """测试获取当前用户信息"""
    response = authenticated_client.get(f"{settings.API_PREFIX}/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_get_current_user_no_token(client: TestClient):
    """测试无 token 获取当前用户"""
    response = client.get(f"{settings.API_PREFIX}/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client: TestClient):
    """测试无效 token 获取当前用户"""
    response = client.get(
        f"{settings.API_PREFIX}/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_refresh_token(client: TestClient):
    """测试刷新 token"""
    register_response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    refresh_token = register_response.json()["refresh_token"]
    
    response = client.post(
        f"{settings.API_PREFIX}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_invalid(client: TestClient):
    """测试无效的刷新 token"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


def test_protected_route(authenticated_client: TestClient):
    """测试受保护的路由 (GET /me)"""
    response = authenticated_client.get(f"{settings.API_PREFIX}/auth/me")
    assert response.status_code == 200
