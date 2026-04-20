
"""
Settings 模型 - 用户全局配置
"""

from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Settings(Base):
    """
    用户全局配置模型
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # 分段配置
    segmentation_config = Column(JSON, default=lambda: {
        "min_length": 50,
        "max_length": 200,
        "detect_chapters": True
    })
    
    # TTS 配置
    tts_config = Column(JSON, default=lambda: {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+0%",
        "pitch": "+0Hz"
    })
    
    # 图像生成配置
    image_config = Column(JSON, default=lambda: {
        "provider": "dalle",
        "style": "anime",
        "resolution": "1024x1024"
    })
    
    # 视频配置
    video_config = Column(JSON, default=lambda: {
        "resolution": "1920x1080",
        "fps": 30,
        "transition": "fade"
    })
    
    # 通知偏好
    notification_config = Column(JSON, default=lambda: {
        "email_notification": False,
        "web_notification": True,
        "progress_update_interval": 10
    })
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="settings")

