"""
提示词优化服务
"""
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings


class PromptService:
    """提示词优化服务"""
    
    @staticmethod
    async def extract_scene_elements(text: str) -> Dict[str, Any]:
        """
        从文本中提取场景元素
        
        Args:
            text: 输入文本
            
        Returns:
            场景元素字典
        """
        # 简单的场景元素提取
        elements = {
            "characters": [],
            "environment": "",
            "atmosphere": "",
            "style": ""
        }
        
        # 这里可以添加更复杂的 NLP 分析
        # 目前返回基础结构
        
        return {
            "success": True,
            "text": text,
            "elements": elements
        }
    
    @staticmethod
    async def translate_to_english(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        将中文文本翻译成英文（用于图像生成）
        
        Args:
            text: 中文文本
            api_key: OpenAI API Key
            
        Returns:
            翻译结果
        """
        key = api_key or settings.OPENAI_API_KEY
        
        if not key:
            # 如果没有 API Key，返回原文
            return {
                "success": True,
                "original": text,
                "translated": text
            }
        
        # 使用 OpenAI API 翻译
        try:
            url = f"{settings.OPENAI_BASE_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate the given Chinese text to English. Keep the meaning intact and use natural English."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                
                translated = result["choices"][0]["message"]["content"].strip()
                
                return {
                    "success": True,
                    "original": text,
                    "translated": translated
                }
        except Exception:
            return {
                "success": True,
                "original": text,
                "translated": text  # 失败时返回原文
            }
    
    @staticmethod
    async def enhance_prompt(
        text: str,
        style: str = "anime",
        enhance_style: bool = True,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        增强提示词，使其更适合图像生成
        
        Args:
            text: 原始文本
            style: 风格
            enhance_style: 是否增强风格
            api_key: OpenAI API Key
            
        Returns:
            增强后的提示词
        """
        # 先翻译
        translation = await PromptService.translate_to_english(text, api_key)
        translated_text = translation["translated"]
        
        # 风格描述
        style_descriptions = {
            "anime": "beautiful anime style illustration, high quality, detailed",
            "photorealistic": "photorealistic, 8k, ultra detailed, cinematic lighting",
            "cinematic": "cinematic composition, movie still, dramatic lighting",
            "3d": "3d render, blender, octane render, unreal engine",
            "watercolor": "watercolor painting, artistic, soft lighting",
            "oil_painting": "oil painting, fine art, brush strokes"
        }
        
        style_desc = style_descriptions.get(style, style_descriptions["anime"])
        
        # 基础增强
        enhanced_prompt = f"{translated_text}, {style_desc}"
        
        # 通用增强词
        common_enhancements = [
            "masterpiece",
            "best quality",
            "highly detailed",
            "vibrant colors"
        ]
        
        if enhance_style:
            enhanced_prompt += ", " + ", ".join(common_enhancements)
        
        # 负面提示词
        negative_prompt = ", ".join([
            "low quality",
            "blurry",
            "lowres",
            "bad anatomy",
            "bad hands"
        ])
        
        return {
            "success": True,
            "original": text,
            "translated": translated_text,
            "enhanced": enhanced_prompt,
            "negative_prompt": negative_prompt,
            "style": style
        }
    
    @staticmethod
    async def generate_image_prompt(text: str, style: str = "anime") -> str:
        """
        生成图像提示词
        
        Args:
            text: 原始文本
            style: 风格
            
        Returns:
            图像提示词
        """
        result = await PromptService.enhance_prompt(text, style)
        return result["enhanced"]
    
    @staticmethod
    def get_available_styles() -> list:
        """获取可用的风格列表"""
        return [
            {"id": "anime", "name": "动漫风格"},
            {"id": "photorealistic", "name": "写实风格"},
            {"id": "cinematic", "name": "电影风格"},
            {"id": "3d", "name": "3D风格"},
            {"id": "watercolor", "name": "水彩风格"},
            {"id": "oil_painting", "name": "油画风格"}
        ]
