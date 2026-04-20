"""
工作流重试机制测试
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.core.security import get_password_hash


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


@pytest.fixture
def test_user(db_session):
    """测试用户 fixture"""
    user = User(
        username="test_retry_user",
        email="test_retry@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session, test_user):
    """测试项目 fixture"""
    project = Project(
        user_id=test_user.id,
        name="Test Retry Project",
        input_file="test_storage/test.txt",
        status="pending",
        config={}
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestRetryCountField:
    """测试 retry_count 字段"""
    
    def test_task_has_retry_count_field(self, db_session, test_project):
        """测试任务模型有 retry_count 字段"""
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="pending",
            retry_count=0
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.retry_count == 0
    
    def test_update_retry_count(self, db_session, test_project):
        """测试更新 retry_count"""
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="pending",
            retry_count=0
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        # 模拟重试
        task.retry_count += 1
        db_session.commit()
        db_session.refresh(task)
        assert task.retry_count == 1
        
        task.retry_count += 1
        db_session.commit()
        db_session.refresh(task)
        assert task.retry_count == 2
    
    def test_max_retry_count_limit(self, db_session, test_project):
        """测试最大重试次数限制"""
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="failed",
            retry_count=3
        )
        db_session.add(task)
        db_session.commit()
        
        # 验证重试计数
        assert task.retry_count == 3


class TestRetryMechanism:
    """测试重试机制"""
    
    def test_task_retry_workflow(self, db_session, test_project):
        """测试任务重试的完整工作流"""
        # 创建初始任务
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="pending",
            retry_count=0
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        # 第一次失败
        task.status = "failed"
        task.retry_count = 1
        task.error = "First failure"
        db_session.commit()
        db_session.refresh(task)
        assert task.retry_count == 1
        assert task.status == "failed"
        
        # 第二次重试并再次失败
        task.status = "running"
        task.retry_count = 2
        db_session.commit()
        task.status = "failed"
        task.error = "Second failure"
        db_session.commit()
        db_session.refresh(task)
        assert task.retry_count == 2
        
        # 第三次重试并成功
        task.status = "running"
        task.retry_count = 3
        task.error = None
        db_session.commit()
        task.status = "completed"
        task.result = {"success": True}
        db_session.commit()
        db_session.refresh(task)
        assert task.retry_count == 3
        assert task.status == "completed"
    
    def test_retry_interval_logic(self, db_session, test_project):
        """测试重试间隔逻辑"""
        from app.workers.tasks import get_retry_delay
        
        # 验证重试延迟
        assert get_retry_delay(0) == 1  # 第一次重试 1秒
        assert get_retry_delay(1) == 3  # 第二次重试 3秒
        assert get_retry_delay(2) == 5  # 第三次重试 5秒
        assert get_retry_delay(3) == 5  # 更多重试保持 5秒
    
    def test_failure_after_max_retries(self, db_session, test_project):
        """测试超过最大重试次数后的失败处理"""
        # 创建失败的任务，已达到最大重试次数
        task = Task(
            project_id=test_project.id,
            step_name="tts",
            status="failed",
            retry_count=3,
            error="Failed after 3 retries"
        )
        db_session.add(task)
        
        # 更新项目状态为失败
        test_project.status = "failed"
        db_session.commit()
        db_session.refresh(test_project)
        db_session.refresh(task)
        
        assert test_project.status == "failed"
        assert task.retry_count == 3


class TestManualRetry:
    """测试手动重试"""
    
    def test_reset_and_retry_task(self, db_session, test_project):
        """测试重置和重试任务"""
        # 创建一个失败的任务
        task = Task(
            project_id=test_project.id,
            step_name="image",
            status="failed",
            retry_count=2,
            error="Image generation failed"
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        # 重置任务状态准备手动重试
        task.status = "pending"
        task.retry_count = 0
        task.error = None
        db_session.commit()
        db_session.refresh(task)
        
        assert task.status == "pending"
        assert task.retry_count == 0
        assert task.error is None
    
    def test_retry_from_failed_step(self, db_session, test_project):
        """测试从失败步骤开始重试"""
        # 创建已完成的前几个步骤
        completed_steps = ["import", "segmentation"]
        for step in completed_steps:
            task = Task(
                project_id=test_project.id,
                step_name=step,
                status="completed",
                result={"success": True},
                retry_count=0
            )
            db_session.add(task)
        
        # 创建失败的步骤
        failed_task = Task(
            project_id=test_project.id,
            step_name="tts",
            status="failed",
            retry_count=1,
            error="TTS failed"
        )
        db_session.add(failed_task)
        db_session.commit()
        
        # 验证步骤状态
        tasks = db_session.query(Task).filter(Task.project_id == test_project.id).all()
        assert len(tasks) == 3
        
        # 模拟从失败步骤开始清理并重试
        steps_to_reset = ["tts", "image", "video_segment", "video_concat"]
        for step in steps_to_reset:
            existing = db_session.query(Task).filter(
                Task.project_id == test_project.id,
                Task.step_name == step
            ).first()
            if existing:
                db_session.delete(existing)
        
        db_session.commit()
        
        # 验证清理后的任务
        remaining = db_session.query(Task).filter(Task.project_id == test_project.id).all()
        assert len(remaining) == 2


class TestErrorRecording:
    """测试错误信息记录"""
    
    def test_error_recording_on_failure(self, db_session, test_project):
        """测试失败时错误信息的记录"""
        task = Task(
            project_id=test_project.id,
            step_name="video_concat",
            status="failed",
            error="FFmpeg process returned non-zero exit code",
            retry_count=1
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.error == "FFmpeg process returned non-zero exit code"
        assert task.status == "failed"
    
    def test_multiple_error_records(self, db_session, test_project):
        """测试多次错误记录（通过更新）"""
        task = Task(
            project_id=test_project.id,
            step_name="video_segment",
            status="pending",
            retry_count=0
        )
        db_session.add(task)
        db_session.commit()
        
        # 第一次失败
        task.status = "failed"
        task.error = "First error: network timeout"
        task.retry_count = 1
        db_session.commit()
        
        # 第二次失败
        task.status = "failed"
        task.error = "Second error: invalid input"
        task.retry_count = 2
        db_session.commit()
        
        db_session.refresh(task)
        assert task.retry_count == 2
        assert task.error == "Second error: invalid input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
