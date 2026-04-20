
"""
API Key 管理服务
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.api_key import ApiKey
from app.core.config import settings
from app.api.v1.settings import decrypt_api_key


class ApiKeyService:
    """API Key 服务"""
    
    @staticmethod
    def get_api_key(db, user_id, provider):
        """
        获取用户的 API Key
        
        优先级：用户数据库存储的 Key &gt; 环境变量配置的 Key
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            provider: 提供商名称 (openai, ark, sd_webui)
            
        Returns:
            API Key 或 None
        """
        # 首先尝试从数据库获取
        api_key = db.query(ApiKey).filter(
            ApiKey.user_id == user_id,
            ApiKey.provider == provider
        ).first()
        
        if api_key:
            return decrypt_api_key(api_key.encrypted_key)
        
        # 如果数据库没有，尝试从环境变量获取
        if provider == "openai":
            return settings.OPENAI_API_KEY or None
        elif provider == "ark":
            return settings.ARK_API_KEY or None
        
        return None
    
    @staticmethod
    def get_sd_webui_url(db, user_id):
        """
        获取 SD WebUI URL
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            
        Returns:
            URL 或 None
        """
        # SD WebUI 通常不需要 key，但可以让用户配置 URL
        api_key = db.query(ApiKey).filter(
            ApiKey.user_id == user_id,
            ApiKey.provider == "sd_webui"
        ).first()
        
        if api_key:
            return decrypt_api_key(api_key.encrypted_key)
        
        # 从环境变量获取
        return settings.SD_WEBUI_URL or None

