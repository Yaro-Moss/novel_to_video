"""
测试批量导出 API
"""
import pytest
from pathlib import Path
from app.core.config import settings


@pytest.fixture
def setup_test_output_dir():
    """设置测试输出目录"""
    project_dir = settings.output_dir_path / "1"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试文件
    (project_dir / "final_video.mp4").write_bytes(b"test video")
    audio_dir = project_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    (audio_dir / "segment_0.mp3").write_bytes(b"test audio 0")
    (audio_dir / "segment_1.mp3").write_bytes(b"test audio 1")
    images_dir = project_dir / "images"
    images_dir.mkdir(exist_ok=True)
    (images_dir / "segment_0.png").write_bytes(b"test image 0")
    (images_dir / "segment_1.png").write_bytes(b"test image 1")
    (project_dir / "subtitles.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nTest subtitle")
    
    yield project_dir
    
    # 清理
    import shutil
    if project_dir.exists():
        shutil.rmtree(project_dir)
    exports_dir = settings.output_dir_path / "exports"
    if exports_dir.exists():
        shutil.rmtree(exports_dir)


@pytest.fixture
def test_project(db_session, test_user):
    """创建测试项目"""
    from app.models.project import Project
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        input_file="test.txt",
        status="pending",
        config={}
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_create_export_task_unauthorized(client):
    """测试未授权创建导出任务"""
    response = client.post("/api/v1/projects/1/export")
    assert response.status_code == 401


def test_create_export_task_nonexistent_project(authenticated_client):
    """测试为不存在的项目创建导出任务"""
    response = authenticated_client.post("/api/v1/projects/99999/export")
    assert response.status_code == 404


def test_create_export_task_uncompleted_project(authenticated_client, test_project):
    """测试为未完成的项目创建导出任务"""
    response = authenticated_client.post(f"/api/v1/projects/{test_project.id}/export")
    assert response.status_code == 400
    assert "只能导出来已完成的项目" in response.json()["detail"]


def test_create_export_task_success(authenticated_client, test_project, db_session, setup_test_output_dir):
    """测试成功创建导出任务"""
    # 标记项目为已完成
    test_project.status = "completed"
    db_session.commit()
    
    # 创建导出任务
    response = authenticated_client.post(
        f"/api/v1/projects/{test_project.id}/export",
        json={
            "include_video": True,
            "include_audio": True,
            "include_images": True,
            "include_subtitles": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "export_id" in data
    assert data["status"] == "processing"
    assert "导出任务已创建" in data["message"]


def test_get_export_status_nonexistent(authenticated_client, test_project):
    """测试获取不存在的导出任务状态"""
    response = authenticated_client.get(f"/api/v1/projects/{test_project.id}/export/nonexistent-id/status")
    assert response.status_code == 404
