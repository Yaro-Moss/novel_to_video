"""
工作流任务测试
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
        username="test_workflow_user",
        email="test_workflow@example.com",
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
        name="Test Workflow Project",
        input_file="test_storage/test.txt",
        status="pending",
        config={}
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestTaskModel:
    """测试 Task 模型"""
    
    def test_create_task(self, db_session, test_project):
        """测试创建任务记录"""
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="pending",
            celery_task_id=None
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.id is not None
        assert task.project_id == test_project.id
        assert task.step_name == "import"
        assert task.status == "pending"
        assert task.created_at is not None
    
    def test_update_task_status(self, db_session, test_project):
        """测试更新任务状态"""
        task = Task(
            project_id=test_project.id,
            step_name="segmentation",
            status="pending"
        )
        db_session.add(task)
        db_session.commit()
        
        # 更新状态为运行中
        task.status = "running"
        db_session.commit()
        db_session.refresh(task)
        assert task.status == "running"
        
        # 更新状态为完成
        task.status = "completed"
        task.result = {"segment_count": 10}
        db_session.commit()
        db_session.refresh(task)
        assert task.status == "completed"
        assert task.result == {"segment_count": 10}
    
    def test_task_error_handling(self, db_session, test_project):
        """测试任务错误处理"""
        task = Task(
            project_id=test_project.id,
            step_name="tts",
            status="failed",
            error="TTS service unavailable"
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        assert task.status == "failed"
        assert task.error == "TTS service unavailable"
    
    def test_task_project_relationship(self, db_session, test_project):
        """测试任务与项目的关系"""
        task = Task(
            project_id=test_project.id,
            step_name="image",
            status="pending"
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        # 从项目访问任务
        db_session.refresh(test_project)
        assert len(test_project.tasks) == 1
        assert test_project.tasks[0].id == task.id


class TestProjectStatusUpdate:
    """测试项目状态更新"""
    
    def test_project_status_processing(self, db_session, test_project):
        """测试项目状态变为处理中"""
        # 创建运行中的任务
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="running"
        )
        db_session.add(task)
        test_project.status = "processing"
        db_session.commit()
        db_session.refresh(test_project)
        
        assert test_project.status == "processing"
    
    def test_project_status_completed(self, db_session, test_project):
        """测试项目状态变为完成"""
        # 创建所有步骤都完成的任务
        steps = ["import", "segmentation", "tts", "image", "video_segment", "video_concat"]
        for step in steps:
            task = Task(
                project_id=test_project.id,
                step_name=step,
                status="completed"
            )
            db_session.add(task)
        
        test_project.status = "completed"
        db_session.commit()
        db_session.refresh(test_project)
        
        assert test_project.status == "completed"
    
    def test_project_status_failed(self, db_session, test_project):
        """测试项目状态变为失败"""
        task = Task(
            project_id=test_project.id,
            step_name="import",
            status="failed",
            error="File not found"
        )
        db_session.add(task)
        test_project.status = "failed"
        db_session.commit()
        db_session.refresh(test_project)
        
        assert test_project.status == "failed"


class TestWorkflowIntegration:
    """工作流集成测试（简化版，不实际运行 Celery）"""
    
    def test_full_workflow_steps(self, db_session, test_project):
        """测试完整工作流步骤顺序"""
        steps = [
            ("import", "导入文本"),
            ("segmentation", "智能分段"),
            ("tts", "TTS 语音合成"),
            ("image", "图像生成"),
            ("video_segment", "视频段生成"),
            ("video_concat", "视频拼接")
        ]
        
        # 模拟执行每个步骤
        for step_name, step_desc in steps:
            task = Task(
                project_id=test_project.id,
                step_name=step_name,
                status="running"
            )
            db_session.add(task)
            db_session.commit()
            
            # 模拟完成
            task.status = "completed"
            task.result = {"step": step_name, "success": True}
            db_session.commit()
        
        # 验证所有步骤都完成
        completed_tasks = db_session.query(Task).filter(
            Task.project_id == test_project.id,
            Task.status == "completed"
        ).all()
        
        assert len(completed_tasks) == 6
        completed_steps = {t.step_name for t in completed_tasks}
        assert completed_steps == {s[0] for s in steps}
    
    def test_workflow_failure_recovery(self, db_session, test_project):
        """测试工作流失败和恢复"""
        # 前两个步骤成功
        for step in ["import", "segmentation"]:
            task = Task(
                project_id=test_project.id,
                step_name=step,
                status="completed",
                result={"success": True}
            )
            db_session.add(task)
        
        # 第三步失败
        failed_task = Task(
            project_id=test_project.id,
            step_name="tts",
            status="failed",
            error="TTS API rate limit exceeded"
        )
        db_session.add(failed_task)
        test_project.status = "failed"
        db_session.commit()
        
        # 模拟重试：清理失败任务，重新开始
        db_session.query(Task).filter(Task.project_id == test_project.id).delete()
        test_project.status = "processing"
        db_session.commit()
        
        # 验证可以重新开始
        assert test_project.status == "processing"
        
        # 重新创建任务
        retry_task = Task(
            project_id=test_project.id,
            step_name="import",
            status="pending"
        )
        db_session.add(retry_task)
        db_session.commit()
        
        assert retry_task.id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
