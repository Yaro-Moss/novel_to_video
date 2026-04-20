
"""
设置相关的 Pydantic schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class ApiKeyCreate(BaseModel):
    provider: str
    api_key: str


class ApiKeyResponse(BaseModel):
    id: int
    provider: str
    masked_key: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 分段配置 Schema
class SegmentationConfig(BaseModel):
    min_length: int = Field(default=50, ge=10, description="最小段落长度")
    max_length: int = Field(default=200, ge=50, description="最大段落长度")
    detect_chapters: bool = Field(default=True, description="是否检测章节")


# TTS 配置 Schema
class TTSConfig(BaseModel):
    voice: str = Field(default="zh-CN-XiaoxiaoNeural", description="TTS 语音")
    rate: str = Field(default="+0%", description="语速")
    pitch: str = Field(default="+0Hz", description="音调")


# 图像配置 Schema
class ImageConfig(BaseModel):
    provider: str = Field(default="dalle", description="图像生成提供商")
    style: str = Field(default="anime", description="图像风格")
    resolution: str = Field(default="1024x1024", description="分辨率")


# 视频配置 Schema
class VideoConfig(BaseModel):
    resolution: str = Field(default="1920x1080", description="视频分辨率")
    fps: int = Field(default=30, ge=1, le=120, description="帧率")
    transition: str = Field(default="fade", description="转场效果")


# 通知配置 Schema
class NotificationConfig(BaseModel):
    email_notification: bool = Field(default=False, description="邮件通知")
    web_notification: bool = Field(default=True, description="网页通知")
    progress_update_interval: int = Field(default=10, ge=1, description="进度更新间隔(秒)")


# 全局设置响应 Schema
class SettingsResponse(BaseModel):
    id: int
    segmentation_config: SegmentationConfig
    tts_config: TTSConfig
    image_config: ImageConfig
    video_config: VideoConfig
    notification_config: NotificationConfig
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# 设置更新请求 Schema (支持部分更新)
class SettingsUpdate(BaseModel):
    segmentation_config: Optional[Dict[str, Any]] = None
    tts_config: Optional[Dict[str, Any]] = None
    image_config: Optional[Dict[str, Any]] = None
    video_config: Optional[Dict[str, Any]] = None
    notification_config: Optional[Dict[str, Any]] = None


