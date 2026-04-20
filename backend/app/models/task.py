"""
任务模型 - 记录工作流各步骤执行状态
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    step_name = Column(String(100), nullable=False)  # import, segmentation, tts, image, video_segment, video_concat
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    result = Column(JSON, nullable=True)  # 存储步骤结果
    error = Column(Text, nullable=True)  # 错误信息
    celery_task_id = Column(String(255), nullable=True, index=True)  # Celery 任务ID
    retry_count = Column(Integer, default=0)  # 重试次数
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    project = relationship("Project", back_populates="tasks")
