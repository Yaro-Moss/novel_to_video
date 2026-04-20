"""
Stable Diffusion WebUI 图像生成服务
"""
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings


class SDWebUIService:
    """Stable Diffusion WebUI 图像生成服务"""
    
    @staticmethod
    async def check_connection(base_url: Optional[str] = None) -> bool:
        """
        检查 SD WebUI 连接
        
        Args:
            base_url: SD WebUI 基础 URL
            
        Returns:
            是否连接成功
        """
        url = base_url or settings.SD_WEBUI_URL
        if not url:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}/sdapi/v1/samplers")
                return response.status_code == 200
        except Exception:
            return False
    
    @staticmethod
    async def generate_image(
        prompt: str,
        negative_prompt: str = "",
        sampler: str = "Euler a",
        steps: int = 28,
        cfg_scale: float = 7.0,
        width: int = 1024,
        height: int = 1024,
        seed: int = -1,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 SD WebUI 生成图像
        
        Args:
            prompt: 提示词
            negative_prompt: 负面提示词
            sampler: 采样器
            steps: 采样步数
            cfg_scale: CFG 比例
            width: 图像宽度
            height: 图像高度
            seed: 随机种子
            base_url: SD WebUI URL
            
        Returns:
            包含 base64 图像数据的字典
        """
        url = base_url or settings.SD_WEBUI_URL
        if not url:
            raise ValueError("SD WebUI URL 未配置")
        
        api_url = f"{url}/sdapi/v1/txt2img"
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "sampler_name": sampler,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "seed": seed,
            "batch_size": 1
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(api_url, json=data)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "image_base64": result["images"][0],
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "sampler": sampler,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "width": width,
                "height": height,
                "seed": result.get("parameters", {}).get("seed", seed),
                "info": result.get("info", "")
            }
    
    @staticmethod
    async def save_base64_image(
        image_base64: str,
        output_path: Path
    ) -> Dict[str, Any]:
        """
        保存 base64 编码的图像到文件
        
        Args:
            image_base64: base64 图像数据
            output_path: 输出文件路径
            
        Returns:
            包含文件信息的字典
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 移除可能的 data URL 前缀
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        # 解码并保存
        image_data = base64.b64decode(image_base64)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return {
            "success": True,
            "file_path": str(output_path),
            "file_size": len(image_data)
        }
    
    @staticmethod
    async def generate_and_save(
        prompt: str,
        output_path: Path,
        negative_prompt: str = "",
        sampler: str = "Euler a",
        steps: int = 28,
        cfg_scale: float = 7.0,
        width: int = 1024,
        height: int = 1024,
        seed: int = -1,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成图像并保存到文件
        
        Args:
            prompt: 提示词
            output_path: 输出文件路径
            ...其他参数...
            
        Returns:
            包含生成信息的字典
        """
        # 生成图像
        result = await SDWebUIService.generate_image(
            prompt, negative_prompt, sampler, steps,
            cfg_scale, width, height, seed, base_url
        )
        
        # 保存图像
        save_result = await SDWebUIService.save_base64_image(
            result["image_base64"], output_path
        )
        
        return {
            **result,
            **save_result,
            "image_base64": None  # 移除 base64 数据节省内存
        }
    
    @staticmethod
    async def get_samplers(base_url: Optional[str] = None) -> list:
        """获取可用的采样器列表"""
        url = base_url or settings.SD_WEBUI_URL
        if not url:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}/sdapi/v1/samplers")
                if response.status_code == 200:
                    return [s["name"] for s in response.json()]
        except Exception:
            pass
        
        return ["Euler a", "Euler", "DPM++ 2M", "DPM++ SDE", "LMS"]
