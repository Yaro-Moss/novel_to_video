"""
DALL-E 图像生成服务
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings


class DALLEService:
    """DALL-E 图像生成服务"""
    
    @staticmethod
    async def generate_image(
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 DALL-E 生成图像
        
        Args:
            prompt: 提示词
            size: 图像尺寸
            quality: 图像质量
            style: 图像风格
            api_key: OpenAI API Key（可选，默认从配置读取）
            
        Returns:
            包含图像 URL 和信息的字典
        """
        key = api_key or settings.OPENAI_API_KEY
        if not key:
            raise ValueError("OpenAI API Key 未配置")
        
        url = f"{settings.OPENAI_BASE_URL}/images/generations"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "style": style
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "image_url": result["data"][0]["url"],
                "revised_prompt": result["data"][0].get("revised_prompt", prompt),
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "style": style
            }
    
    @staticmethod
    async def download_image(
        image_url: str,
        output_path: Path
    ) -> Dict[str, Any]:
        """
        下载图像到本地文件
        
        Args:
            image_url: 图像 URL
            output_path: 输出文件路径
            
        Returns:
            包含文件信息的字典
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return {
                "success": True,
                "file_path": str(output_path),
                "file_size": len(response.content)
            }
    
    @staticmethod
    async def generate_and_save(
        prompt: str,
        output_path: Path,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成图像并保存到文件
        
        Args:
            prompt: 提示词
            output_path: 输出文件路径
            size: 图像尺寸
            quality: 图像质量
            style: 图像风格
            api_key: OpenAI API Key
            
        Returns:
            包含生成信息的字典
        """
        # 生成图像
        result = await DALLEService.generate_image(
            prompt, size, quality, style, api_key
        )
        
        # 下载图像
        download_result = await DALLEService.download_image(
            result["image_url"], output_path
        )
        
        return {
            **result,
            **download_result
        }
    
    @staticmethod
    def get_available_sizes() -> list:
        """获取可用的图像尺寸"""
        return ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]
    
    @staticmethod
    def get_available_qualities() -> list:
        """获取可用的图像质量"""
        return ["standard", "hd"]
    
    @staticmethod
    def get_available_styles() -> list:
        """获取可用的图像风格"""
        return ["vivid", "natural"]
