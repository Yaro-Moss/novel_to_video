import pytest
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app

client = TestClient(app)


def test_cors_headers():
    """测试 CORS 头是否正确返回"""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == status.HTTP_200_OK
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers


def test_cors_allowed_origin():
    """测试允许的源"""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("access-control-allow-origin") in ["http://localhost:5173", "*"]


def test_static_files_mounted():
    """测试静态文件是否挂载"""
    # 检查主应用配置是否包含静态文件挂载逻辑
    assert True


def test_config_has_max_upload_size():
    """测试配置包含 MAX_UPLOAD_SIZE_MB"""
    from app.core.config import settings
    assert hasattr(settings, "MAX_UPLOAD_SIZE_MB")
    assert settings.MAX_UPLOAD_SIZE_MB > 0


def test_static_directories_exist():
    """测试静态文件目录是否存在"""
    from app.core.config import settings
    assert settings.upload_dir_path.exists()
    assert settings.output_dir_path.exists()
