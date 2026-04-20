"""
图像生成 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import DALLEService, SDWebUIService, PromptService

router = APIRouter(prefix="/images", tags=["images"])


class DALLEGenerateRequest(BaseModel):
    """DALL-E 图像生成请求"""
    prompt: str = Field(..., min_length=1, description="提示词")
    size: str = Field(default="1024x1024", description="图像尺寸")
    quality: str = Field(default="standard", description="图像质量")
    style: str = Field(default="vivid", description="图像风格")


class SDGenerateRequest(BaseModel):
    """SD WebUI 图像生成请求"""
    prompt: str = Field(..., min_length=1, description="提示词")
    negative_prompt: str = Field(default="", description="负面提示词")
    sampler: str = Field(default="Euler a", description="采样器")
    steps: int = Field(default=28, ge=1, le=100, description="采样步数")
    cfg_scale: float = Field(default=7.0, ge=1.0, le=20.0, description="CFG 比例")
    width: int = Field(default=1024, description="宽度")
    height: int = Field(default=1024, description="高度")
    seed: int = Field(default=-1, description="随机种子")


class PromptEnhanceRequest(BaseModel):
    """提示词优化请求"""
    text: str = Field(..., min_length=1, description="原始文本")
    style: str = Field(default="anime", description="风格")
    enhance_style: bool = Field(default=True, description="是否增强风格")


@router.get("/engines")
async def list_engines():
    """列出可用的图像生成引擎"""
    return {
        "success": True,
        "engines": [
            {"id": "dalle", "name": "DALL-E 3"},
            {"id": "sd_webui", "name": "Stable Diffusion WebUI"}
        ]
    }


@router.get("/dalle/config")
async def get_dalle_config():
    """获取 DALL-E 可用配置"""
    return {
        "success": True,
        "sizes": DALLEService.get_available_sizes(),
        "qualities": DALLEService.get_available_qualities(),
        "styles": DALLEService.get_available_styles()
    }


@router.post("/dalle/generate")
async def generate_with_dalle(
    request: DALLEGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """使用 DALL-E 生成图像"""
    try:
        result = await DALLEService.generate_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            style=request.style
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DALL-E 图像生成失败: {str(e)}"
        )


@router.get("/sd_webui/config")
async def get_sd_config():
    """获取 SD WebUI 可用配置"""
    sd_connected = await SDWebUIService.check_connection()
    samplers = await SDWebUIService.get_samplers()
    return {
        "success": True,
        "connected": sd_connected,
        "samplers": samplers
    }


@router.get("/sd_webui/check")
async def check_sd_connection():
    """检查 SD WebUI 连接"""
    connected = await SDWebUIService.check_connection()
    return {
        "success": True,
        "connected": connected
    }


@router.post("/sd_webui/generate")
async def generate_with_sd(
    request: SDGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """使用 SD WebUI 生成图像"""
    try:
        result = await SDWebUIService.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            sampler=request.sampler,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            width=request.width,
            height=request.height,
            seed=request.seed
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SD WebUI 图像生成失败: {str(e)}"
        )


@router.get("/prompt/styles")
async def get_prompt_styles():
    """获取可用的风格列表"""
    return {
        "success": True,
        "styles": PromptService.get_available_styles()
    }


@router.post("/prompt/enhance")
async def enhance_prompt(
    request: PromptEnhanceRequest,
    current_user: User = Depends(get_current_user)
):
    """优化提示词"""
    try:
        result = await PromptService.enhance_prompt(
            text=request.text,
            style=request.style,
            enhance_style=request.enhance_style
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提示词优化失败: {str(e)}"
        )
