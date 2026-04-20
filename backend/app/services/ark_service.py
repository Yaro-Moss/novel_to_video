"""
火山方舟（豆包）图像生成服务
使用官方 volcenginesdkarkruntime SDK
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from volcenginesdkarkruntime import Ark
    HAS_ARK_SDK = True
except ImportError:
    HAS_ARK_SDK = False
    logging.warning("未安装火山方舟SDK，请运行: pip install 'volcengine-python-sdk[ark]'")

from app.core.config import settings

logger = logging.getLogger(__name__)


class ARKService:
    """火山方舟图像生成服务"""
    
    @staticmethod
    def _generate_placeholder_image(size: str = "2K") -> bytes:
        """
        生成一个简单的占位图像作为fallback
        
        Args:
            size: 图像尺寸，格式为"宽x高"
            
        Returns:
            PNG格式的图像数据
        """
        try:
            width, height = map(int, size.split("x"))
        except:
            width, height = 1024, 1024
        
        # 使用PIL生成简单的占位图像
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # 创建渐变背景
            img = Image.new('RGB', (width, height), color=(70, 130, 180))
            draw = ImageDraw.Draw(img)
            
            # 添加一些装饰性的图形
            for i in range(0, width, 50):
                draw.line([(i, 0), (i, height)], fill=(100, 149, 237), width=2)
            for i in range(0, height, 50):
                draw.line([(0, i), (width, i)], fill=(100, 149, 237), width=2)
            
            # 添加文字
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            text = "小说转视频\nPlaceholder Image"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (width - text_width) / 2
            text_y = (height - text_height) / 2
            
            draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer.read()
            
        except ImportError:
            # 如果PIL不可用，生成一个简单的1x1 PNG
            return (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                b'\x0d\n-\x94\x00\x00\x00\x00IEND\xaeB`\x82'
            )
    
    @staticmethod
    async def generate_image(
        prompt: str,
        size: str = "2K",
        quality: str = "standard",
        style: str = "vivid",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用火山方舟SDK生成图像
        
        Args:
            prompt: 提示词
            size: 图像尺寸
            quality: 图像质量（保留用于兼容性）
            style: 图像风格（保留用于兼容性）
            api_key: 火山方舟 API Key（可选，默认从配置读取）
            base_url: 火山方舟 API 基础地址（可选，默认从配置读取）
            
        Returns:
            包含图像 URL 和信息的字典
        """
        if not HAS_ARK_SDK:
            raise ImportError("火山方舟SDK未安装，请运行: pip install 'volcengine-python-sdk[ark]'")
        
        key = api_key or settings.ARK_API_KEY
        url = base_url or settings.ARK_BASE_URL
        
        if not key:
            raise ValueError("火山方舟 API Key 未配置")
        if not url:
            raise ValueError("火山方舟 API 地址未配置")
        
        logger.info(f"使用火山方舟SDK生成图像，size={size}")
        logger.debug(f"Prompt: {prompt[:100]}...")
        
        # 初始化Ark客户端
        client = Ark(
            base_url=url,
            api_key=key
        )
        
        ark_size = size
        valid_sizes = ["512x512", "768x768", "1024x1024", "1280x768", "768x1280", "2K"]
        if size not in valid_sizes:
            ark_size = "2K"
        
        # 使用SDK调用
        images_response = client.images.generate(
            model="doubao-seedream-4-5-251128",
            prompt=prompt,
            sequential_image_generation="disabled",
            response_format="url",
            size=ark_size,
            stream=False,
            watermark=True
        )
        
        image_url = images_response.data[0].url
        logger.info(f"图像生成成功: {image_url}")
        
        return {
            "success": True,
            "image_url": image_url,
            "revised_prompt": prompt,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "style": style,
            "use_fallback": False
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
        
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return {
                "success": True,
                "file_path": str(output_path),
                "file_size": len(response.content),
                "use_fallback": False
            }
    
    @staticmethod
    async def generate_and_save(
        prompt: str,
        output_path: Path,
        size: str = "2K",
        quality: str = "standard",
        style: str = "vivid",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成图像并保存到文件
        
        Args:
            prompt: 提示词
            output_path: 输出文件路径
            size: 图像尺寸
            quality: 图像质量
            style: 图像风格
            api_key: 火山方舟 API Key
            base_url: 火山方舟 API 基础地址
            
        Returns:
            包含生成信息的字典
        """
        # 生成图像
        result = await ARKService.generate_image(
            prompt, size, quality, style, api_key, base_url
        )
        
        # 下载图像
        download_result = await ARKService.download_image(
            result["image_url"], output_path
        )
        
        return {**result, **download_result}
    
    @staticmethod
    def get_available_sizes() -> list:
        """获取可用的图像尺寸"""
        return ["512x512", "768x768", "1024x1024", "1280x768", "768x1280", "2K"]
    
    @staticmethod
    def get_available_qualities() -> list:
        """获取可用的图像质量"""
        return ["standard", "hd"]
    
    @staticmethod
    def get_available_styles() -> list:
        """获取可用的图像风格"""
        return ["vivid", "natural"]
