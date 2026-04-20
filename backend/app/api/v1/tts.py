"""
TTS API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import TTSService

router = APIRouter(prefix="/tts", tags=["tts"])


class PreviewRequest(BaseModel):
    """TTS 预览请求"""
    text: str = Field(..., min_length=1, max_length=500, description="要合成的文本")
    voice: str = Field(default="zh-CN-XiaoxiaoNeural", description="语音ID")
    rate: str = Field(default="+0%", description="语速")
    volume: str = Field(default="+0%", description="音量")
    pitch: str = Field(default="+0Hz", description="音调")


@router.get("/voices")
async def list_voices(
    current_user: User = Depends(get_current_user),
):
    """
    获取可用语音列表
    
    Returns:
        语音列表
    """
    try:
        voices = await TTSService.get_voices()
        return {
            "success": True,
            "data": voices,
            "total": len(voices)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取语音列表失败: {str(e)}"
        )


@router.post("/preview")
async def preview_tts(
    request: PreviewRequest,
    current_user: User = Depends(get_current_user),
):
    """
    TTS 预览（生成并返回音频）
    
    Args:
        request: 预览请求参数
        
    Returns:
        音频流
    """
    try:
        # 限制文本长度（防止滥用）
        if len(request.text) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="预览文本长度不能超过 500 字符"
            )
        
        # 合成音频
        audio_data = await TTSService.synthesize(
            request.text,
            request.voice,
            request.rate,
            request.volume,
            request.pitch
        )
        
        # 返回音频流
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=preview.mp3"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS 预览失败: {str(e)}"
        )
