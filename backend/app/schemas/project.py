"""
项目相关的 Pydantic schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    config: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    input_file: str
    status: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int


class ProjectStatusResponse(BaseModel):
    project_id: int
    status: str
    current_step: Optional[str] = None
    percentage: float = 0.0
    elapsed_time: Optional[float] = None
    estimated_remaining: Optional[float] = None
    tasks: list[dict] = []


class SegmentResponse(BaseModel):
    index: int
    text: str
    char_count: int
    chapter_title: Optional[str] = None


class SegmentsResponse(BaseModel):
    segments: list[SegmentResponse]
    total_count: int
    total_chars: int


class ExportRequest(BaseModel):
    include_video: bool = True
    include_audio: bool = True
    include_images: bool = True
    include_subtitles: bool = True


class ExportResponse(BaseModel):
    export_id: str
    status: str
    message: str


class ExportStatusResponse(BaseModel):
    export_id: str
    status: str
    progress: float = 0.0
    message: str = ""
    file_size: int = 0
