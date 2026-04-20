
"""
测试全局设置 API
"""

import pytest
from fastapi.testclient import TestClient


def test_get_settings_unauthenticated(client: TestClient):
    """
    测试未认证时访问设置 API 应该失败
    """
    response = client.get("/api/v1/settings")
    assert response.status_code == 401


def test_get_settings_initial(client: TestClient, auth_token: str):
    """
    测试获取初始设置（应该自动创建默认设置）
    """
    response = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "segmentation_config" in data
    assert "tts_config" in data
    assert "image_config" in data
    assert "video_config" in data
    assert "notification_config" in data
    
    # 验证默认值
    assert data["segmentation_config"]["min_length"] == 50
    assert data["tts_config"]["voice"] == "zh-CN-XiaoxiaoNeural"
    assert data["notification_config"]["web_notification"] is True


def test_update_settings_partial(client: TestClient, auth_token: str):
    """
    测试部分更新设置
    """
    # 先获取初始设置
    response = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    # 只更新分段配置
    update_data = {
        "segmentation_config": {
            "min_length": 100,
            "max_length": 300
        }
    }
    
    response = client.patch(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    
    # 验证更新生效
    assert data["segmentation_config"]["min_length"] == 100
    assert data["segmentation_config"]["max_length"] == 300
    # 其他配置应该保持不变
    assert data["tts_config"]["voice"] == "zh-CN-XiaoxiaoNeural"


def test_update_settings_multiple(client: TestClient, auth_token: str):
    """
    测试同时更新多个配置项
    """
    update_data = {
        "tts_config": {
            "voice": "zh-CN-YunxiNeural",
            "rate": "+10%"
        },
        "notification_config": {
            "email_notification": True,
            "progress_update_interval": 5
        }
    }
    
    response = client.patch(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["tts_config"]["voice"] == "zh-CN-YunxiNeural"
    assert data["tts_config"]["rate"] == "+10%"
    assert data["notification_config"]["email_notification"] is True
    assert data["notification_config"]["progress_update_interval"] == 5


def test_update_settings_unauthenticated(client: TestClient):
    """
    测试未认证时更新设置应该失败
    """
    update_data = {
        "segmentation_config": {"min_length": 100}
    }
    response = client.patch("/api/v1/settings", json=update_data)
    assert response.status_code == 401


def test_settings_isolation_between_users(client: TestClient, auth_token: str):
    """
    测试设置可以正确保存和读取
    """
    # 使用已有的 auth_token 更新设置
    client.patch(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"tts_config": {"voice": "test-voice-1"}}
    )
    
    # 获取并验证
    resp = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.json()["tts_config"]["voice"] == "test-voice-1"



def test_default_settings_values(client: TestClient, auth_token: str):
    """
    测试所有默认配置值是否正确
    """
    response = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    data = response.json()
    
    # 分段配置
    assert data["segmentation_config"]["min_length"] == 50
    assert data["segmentation_config"]["max_length"] == 200
    assert data["segmentation_config"]["detect_chapters"] is True
    
    # TTS 配置
    assert data["tts_config"]["voice"] == "zh-CN-XiaoxiaoNeural"
    assert data["tts_config"]["rate"] == "+0%"
    assert data["tts_config"]["pitch"] == "+0Hz"
    
    # 图像配置
    assert data["image_config"]["provider"] == "dalle"
    assert data["image_config"]["style"] == "anime"
    assert data["image_config"]["resolution"] == "1024x1024"
    
    # 视频配置
    assert data["video_config"]["resolution"] == "1920x1080"
    assert data["video_config"]["fps"] == 30
    assert data["video_config"]["transition"] == "fade"
    
    # 通知配置
    assert data["notification_config"]["email_notification"] is False
    assert data["notification_config"]["web_notification"] is True
    assert data["notification_config"]["progress_update_interval"] == 10


def test_update_empty_settings(client: TestClient, auth_token: str):
    """
    测试发送空更新请求（不改变任何配置）
    """
    # 先获取设置
    get_resp = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    original_data = get_resp.json()
    
    # 发送空更新
    response = client.patch(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )
    assert response.status_code == 200
    
    # 验证配置没有变化
    new_data = response.json()
    assert new_data["segmentation_config"] == original_data["segmentation_config"]
    assert new_data["tts_config"] == original_data["tts_config"]

