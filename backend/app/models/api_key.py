"""
API Key 模型 - 安全存储用户的 API Key
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # openai, sd_webui, etc.
    encrypted_key = Column(String(500), nullable=False)  # 使用 Fernet 加密存储
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # 关系
    user = relationship("User", back_populates="api_keys")
