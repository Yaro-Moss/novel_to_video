
"""
设置管理 API - API Key 管理和全局配置
"""

import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from cryptography.fernet import Fernet
from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.settings import Settings
from app.schemas.settings import (
    ApiKeyCreate, ApiKeyResponse,
    SettingsResponse, SettingsUpdate
)

router = APIRouter(prefix="/settings", tags=["settings"])


def get_fernet():
    """从 SECRET_KEY 生成固定的 Fernet 密钥"""
    secret_key = settings.SECRET_KEY.encode('utf-8')
    # 将密钥填充或截断到 32 字节，然后用 base64 编码
    if len(secret_key) < 32:
        secret_key = secret_key.ljust(32, b'=')
    elif len(secret_key) > 32:
        secret_key = secret_key[:32]
    # Fernet 需要 URL-safe base64 编码的 32 字节密钥
    fernet_key = base64.urlsafe_b64encode(secret_key)
    return Fernet(fernet_key)


def encrypt_api_key(key):
    """加密 API Key"""
    fernet = get_fernet()
    return fernet.encrypt(key.encode('utf-8')).decode('utf-8')


def decrypt_api_key(encrypted_key):
    """解密 API Key"""
    fernet = get_fernet()
    return fernet.decrypt(encrypted_key.encode('utf-8')).decode('utf-8')


def get_user_api_key(db, user_id, provider):
    """获取用户的 API Key（解密后的）"""
    api_key = db.query(ApiKey).filter(
        ApiKey.user_id == user_id,
        ApiKey.provider == provider
    ).first()
    if api_key:
        return decrypt_api_key(api_key.encrypted_key)
    return None


def mask_api_key(key):
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]


def get_or_create_user_settings(db, user_id):
    """
    获取或创建用户设置
    """
    settings_obj = db.query(Settings).filter(Settings.user_id == user_id).first()
    if not settings_obj:
        settings_obj = Settings(user_id=user_id)
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)
    return settings_obj


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的全局配置
    """
    settings_obj = get_or_create_user_settings(db, current_user.id)
    return settings_obj


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    settings_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新当前用户的全局配置（支持部分更新）
    """
    settings_obj = get_or_create_user_settings(db, current_user.id)
    modified = False
    
    # 更新各个配置项 - 确保 SQLAlchemy 检测到更改
    if settings_data.segmentation_config is not None:
        current = dict(settings_obj.segmentation_config or {})
        current.update(settings_data.segmentation_config)
        settings_obj.segmentation_config = current
        flag_modified(settings_obj, "segmentation_config")
        modified = True
    
    if settings_data.tts_config is not None:
        current = dict(settings_obj.tts_config or {})
        current.update(settings_data.tts_config)
        settings_obj.tts_config = current
        flag_modified(settings_obj, "tts_config")
        modified = True
    
    if settings_data.image_config is not None:
        current = dict(settings_obj.image_config or {})
        current.update(settings_data.image_config)
        settings_obj.image_config = current
        flag_modified(settings_obj, "image_config")
        modified = True
    
    if settings_data.video_config is not None:
        current = dict(settings_obj.video_config or {})
        current.update(settings_data.video_config)
        settings_obj.video_config = current
        flag_modified(settings_obj, "video_config")
        modified = True
    
    if settings_data.notification_config is not None:
        current = dict(settings_obj.notification_config or {})
        current.update(settings_data.notification_config)
        settings_obj.notification_config = current
        flag_modified(settings_obj, "notification_config")
        modified = True
    
    db.commit()
    db.refresh(settings_obj)
    return settings_obj


@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    添加新的 API Key
    """
    # 检查是否已存在该 provider 的 key，先删除
    existing_key = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.provider == api_key_data.provider
    ).first()
    if existing_key:
        db.delete(existing_key)
    
    # 加密并保存新 key
    encrypted_key = encrypt_api_key(api_key_data.api_key)

    api_key = ApiKey(
        user_id=current_user.id,
        provider=api_key_data.provider,
        encrypted_key=encrypted_key
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        masked_key=mask_api_key(api_key_data.api_key),
        created_at=api_key.created_at
    )


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的 API Key 列表（脱敏显示）
    """
    api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
    
    return [
        ApiKeyResponse(
            id=key.id,
            provider=key.provider,
            masked_key=mask_api_key(decrypt_api_key(key.encrypted_key)),
            created_at=key.created_at
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除指定的 API Key
    """
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
    
    db.delete(api_key)
    db.commit()
    
    return None

