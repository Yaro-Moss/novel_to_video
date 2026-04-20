"""
简化工作流模块 - 不依赖 Celery，直接在后台执行
"""
import asyncio
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.websocket_manager import (
    send_progress_update,
    send_step_complete,
    send_step_failed
)
from app.models.project import Project
from app.models.task import Task
from app.services.text_import_service import TextImportService
from app.services.segmentation_service import SegmentationService
from app.services.tts_service import TTSService
from app.services.prompt_service import PromptService
from app.services.dalle_service import DALLEService
from app.services.video_segment_service import VideoSegmentService
from app.services.video_concat_service import VideoConcatService
from app.services.ark_service import ARKService
from app.services.sd_webui_service import SDWebUIService

logger = logging.getLogger(__name__)

# 活跃工作流追踪
active_workflows: Dict[int, threading.Thread] = {}


def _get_image_provider_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """从配置中获取图像提供商的配置"""
    image_engine = config.get("image_engine", "ark")
    
    if image_engine == "ark":
        return {
            "provider": "ark",
            "config": config.get("ark", {})
        }
    elif image_engine == "sd_webui":
        return {
            "provider": "sd_webui",
            "config": config.get("sd_webui", {})
        }
    else:
        return {
            "provider": "dalle",
            "config": config.get("dalle", {})
        }


async def _update_task_status(
    project_id: int,
    step_name: str,
    status: str,
    result: Dict[str, Any] = None,
    error: str = None,
    increment_retry: bool = False
):
    """更新任务状态到数据库"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(
            Task.project_id == project_id,
            Task.step_name == step_name
        ).first()
        
        if not task:
            task = Task(
                project_id=project_id,
                step_name=step_name,
                status=status,
                result=result,
                error=error,
                retry_count=0
            )
            db.add(task)
        else:
            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if increment_retry:
                task.retry_count = task.retry_count + 1
        
        # 更新项目状态
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            if status == "failed":
                project.status = "failed"
            elif status == "completed" and step_name == "video_concat":
                project.status = "completed"
            elif status == "running":
                project.status = "processing"
        
        db.commit()
        db.refresh(task)
        if project:
            db.refresh(project)
        return task
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def _import_text(project_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """步骤1: 导入文本"""
    logger.info(f"Starting text import for project {project_id}")
    
    await send_progress_update(project_id, "import", 5, "正在读取文本文件...")
    await _update_task_status(project_id, "import", "running")
    
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        await send_progress_update(project_id, "import", 10, "正在解析文本...")
        
        # 导入文本
        text_service = TextImportService()
        # 修复文件路径
        file_path = settings.upload_dir_path.parent / project.input_file
        text_result = text_service.read_file(str(file_path))
        text_content = text_result["cleaned_content"]
        
        result = {
            "text_length": len(text_content),
            "success": True
        }
        
        await _update_task_status(project_id, "import", "completed", result)
        await send_step_complete(project_id, "import", result)
        await send_progress_update(project_id, "import", 15, "文本导入完成", "completed")
        
        logger.info(f"Text import completed for project {project_id}")
        return {"project_id": project_id, "text_content": text_content, "config": config}
    finally:
        db.close()


async def _segmentation(prev_result: Dict[str, Any]) -> Dict[str, Any]:
    """步骤2: 智能分段"""
    project_id = prev_result["project_id"]
    text_content = prev_result["text_content"]
    config = prev_result.get("config", {})
    
    logger.info(f"Starting segmentation for project {project_id}")
    
    await send_progress_update(project_id, "segmentation", 18, "正在进行文本分段...")
    await _update_task_status(project_id, "segmentation", "running")
    
    # 分段
    seg_service = SegmentationService()
    segments = seg_service.segment(
        text_content,
        min_length=config.get("min_length", 100),
        max_length=config.get("max_length", 500),
        detect_chapters=config.get("detect_chapters", True)
    )
    
    await send_progress_update(project_id, "segmentation", 25, f"完成 {len(segments)} 个段落分段")
    
    result = {
        "segment_count": len(segments),
        "total_chars": sum(s['char_count'] for s in segments),
        "success": True
    }
    
    await _update_task_status(project_id, "segmentation", "completed", result)
    await send_step_complete(project_id, "segmentation", result)
    await send_progress_update(project_id, "segmentation", 30, "分段完成", "completed")
    
    logger.info(f"Segmentation completed for project {project_id}")
    return {**prev_result, "segments": segments}


async def _tts(prev_result: Dict[str, Any]) -> Dict[str, Any]:
    """步骤3: TTS 语音合成"""
    project_id = prev_result["project_id"]
    segments = prev_result["segments"]
    config = prev_result.get("config", {})
    
    logger.info(f"Starting TTS for project {project_id}")
    
    await send_progress_update(project_id, "tts", 30, "开始语音合成...")
    await _update_task_status(project_id, "tts", "running")
    
    # 创建输出目录
    project_output_dir = settings.output_dir_path / str(project_id)
    project_output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = project_output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # TTS 合成
    tts_service = TTSService()
    voice = config.get("tts", {}).get("voice", "zh-CN-XiaoxiaoNeural")
    engine = config.get("tts", {}).get("engine", TTSService.TTS_ENGINE_EDGE)
    audio_files = []
    
    total = len(segments)
    for i, segment in enumerate(segments):
        progress = 30 + (i / total) * 18
        await send_progress_update(project_id, "tts", progress, f"正在合成第 {i+1}/{total} 个音频...")
        
        # 根据引擎选择文件扩展名
        ext = "wav" if engine == TTSService.TTS_ENGINE_KOKORO else "mp3"
        audio_path = audio_dir / f"segment_{i:04d}.{ext}"
        
        await tts_service.synthesize_to_file(
            text=segment["text"],
            output_path=audio_path,
            voice=voice,
            engine=engine
        )
        audio_files.append(str(audio_path))
    
    result = {
        "audio_count": len(audio_files),
        "success": True
    }
    
    await _update_task_status(project_id, "tts", "completed", result)
    await send_step_complete(project_id, "tts", result)
    await send_progress_update(project_id, "tts", 50, "音频合成完成", "completed")
    
    logger.info(f"TTS completed for project {project_id}")
    return {**prev_result, "audio_files": audio_files}


async def _images(prev_result: Dict[str, Any]) -> Dict[str, Any]:
    """步骤4: 图像生成"""
    project_id = prev_result["project_id"]
    segments = prev_result["segments"]
    config = prev_result.get("config", {})
    
    logger.info(f"Starting image generation for project {project_id}")
    
    await send_progress_update(project_id, "image", 50, "开始生成图像...")
    await _update_task_status(project_id, "image", "running")
    
    # 创建输出目录
    project_output_dir = settings.output_dir_path / str(project_id)
    images_dir = project_output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取图像提供商配置
    provider_info = _get_image_provider_config(config)
    provider = provider_info["provider"]
    provider_config = provider_info["config"]
    
    # 图像生成
    prompt_service = PromptService()
    image_files = []
    
    total = len(segments)
    for i, segment in enumerate(segments):
        progress = 50 + (i / total) * 23
        await send_progress_update(project_id, "image", progress, f"正在生成第 {i+1}/{total} 张图片...")
        
        # 生成提示词
        prompt = await PromptService.generate_image_prompt(segment["text"])
        
        # 生成图像
        image_path = images_dir / f"segment_{i:04d}.png"
        
        if provider == "dalle":
            dalle_service = DALLEService()
            await dalle_service.generate_and_save(
                prompt=prompt,
                output_path=image_path,
                size=provider_config.get("size", "1024x1024"),
                quality=provider_config.get("quality", "standard"),
                style=provider_config.get("style", "vivid"),
                api_key=settings.OPENAI_API_KEY
            )
        elif provider == "ark":
            ark_service = ARKService()
            await ark_service.generate_and_save(
                prompt=prompt,
                output_path=image_path,
                size=provider_config.get("size", "2K"),
                quality=provider_config.get("quality", "standard"),
                style=provider_config.get("style", "vivid"),
                api_key=settings.ARK_API_KEY
            )
        else:
            sd_service = SDWebUIService()
            await sd_service.generate_and_save(
                prompt=prompt,
                output_path=image_path,
                negative_prompt=provider_config.get("negative_prompt", ""),
                sampler=provider_config.get("sampler", "Euler a"),
                steps=provider_config.get("steps", 28),
                cfg_scale=provider_config.get("cfg_scale", 7.0),
                width=provider_config.get("width", 1024),
                height=provider_config.get("height", 1024),
                seed=provider_config.get("seed", -1),
                base_url=settings.SD_WEBUI_URL
            )
        
        image_files.append(str(image_path))
    
    result = {
        "image_count": len(image_files),
        "success": True
    }
    
    await _update_task_status(project_id, "image", "completed", result)
    await send_step_complete(project_id, "image", result)
    await send_progress_update(project_id, "image", 75, "图像生成完成", "completed")
    
    logger.info(f"Image generation completed for project {project_id}")
    return {**prev_result, "image_files": image_files}


async def _video_segments(prev_result: Dict[str, Any]) -> Dict[str, Any]:
    """步骤5: 视频段生成"""
    project_id = prev_result["project_id"]
    audio_files = prev_result["audio_files"]
    image_files = prev_result["image_files"]
    config = prev_result.get("config", {})
    
    logger.info(f"Starting video segment generation for project {project_id}")
    
    await send_progress_update(project_id, "video_segment", 75, "开始生成视频段...")
    await _update_task_status(project_id, "video_segment", "running")
    
    # 创建输出目录
    project_output_dir = settings.output_dir_path / str(project_id)
    video_segments_dir = project_output_dir / "video_segments"
    video_segments_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成视频段
    video_service = VideoSegmentService()
    video_segment_files = []
    
    total = len(audio_files)
    for i, (audio_file, image_file) in enumerate(zip(audio_files, image_files)):
        progress = 75 + (i / total) * 13
        await send_progress_update(project_id, "video_segment", progress, f"正在生成第 {i+1}/{total} 个视频段...")
        
        video_path = video_segments_dir / f"segment_{i:04d}.mp4"
        await video_service.create_segment_async(
            image_path=Path(image_file),
            audio_path=Path(audio_file),
            output_path=video_path
        )
        video_segment_files.append(str(video_path))
    
    result = {
        "video_segment_count": len(video_segment_files),
        "success": True
    }
    
    await _update_task_status(project_id, "video_segment", "completed", result)
    await send_step_complete(project_id, "video_segment", result)
    await send_progress_update(project_id, "video_segment", 90, "视频段生成完成", "completed")
    
    logger.info(f"Video segment generation completed for project {project_id}")
    return {**prev_result, "video_segment_files": video_segment_files}


async def _video_concat(prev_result: Dict[str, Any]) -> Dict[str, Any]:
    """步骤6: 视频拼接"""
    project_id = prev_result["project_id"]
    video_segment_files = prev_result["video_segment_files"]
    
    logger.info(f"Starting video concatenation for project {project_id}")
    
    await send_progress_update(project_id, "video_concat", 92, "正在拼接视频...")
    await _update_task_status(project_id, "video_concat", "running")
    
    # 创建输出目录
    project_output_dir = settings.output_dir_path / str(project_id)
    
    # 拼接视频
    concat_service = VideoConcatService()
    output_path = project_output_dir / "final_video.mp4"
    
    await concat_service.concat_async(
        video_paths=[Path(v) for v in video_segment_files],
        output_path=output_path
    )
    
    result = {
        "output_path": str(output_path),
        "success": True
    }
    
    await _update_task_status(project_id, "video_concat", "completed", result)
    await send_step_complete(project_id, "video_concat", result)
    await send_progress_update(project_id, "video_concat", 100, "视频生成完成！", "completed")
    
    logger.info(f"Video concatenation completed for project {project_id}")
    return {**prev_result, "final_video_path": str(output_path)}


async def _execute_full_workflow(project_id: int, config: Dict[str, Any] = None):
    """执行完整工作流"""
    logger.info(f"Starting full workflow for project {project_id}")
    
    current_step = None
    
    try:
        # 清理旧的任务记录
        db = SessionLocal()
        try:
            db.query(Task).filter(Task.project_id == project_id).delete()
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = "processing"
                project.config = config or {}
            db.commit()
        finally:
            db.close()
        
        # 步骤1: 导入文本
        current_step = "import"
        step1_result = await _import_text(project_id, config or {})
        
        # 步骤2: 分段
        current_step = "segmentation"
        step2_result = await _segmentation(step1_result)
        
        # 步骤3: TTS
        current_step = "tts"
        step3_result = await _tts(step2_result)
        
        # 步骤4: 图像生成
        current_step = "image"
        step4_result = await _images(step3_result)
        
        # 步骤5: 视频段
        current_step = "video_segment"
        step5_result = await _video_segments(step4_result)
        
        # 步骤6: 视频拼接
        current_step = "video_concat"
        final_result = await _video_concat(step5_result)
        
        logger.info(f"Workflow completed for project {project_id}")
        return final_result
        
    except Exception as e:
        logger.error(f"Workflow failed for project {project_id}: {e}")
        
        # 发送失败通知
        if current_step:
            await send_step_failed(project_id, current_step, str(e))
        
        # 标记失败
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = "failed"
            db.commit()
        finally:
            db.close()
        
        raise


def start_simple_workflow(project_id: int, config: Dict[str, Any] = None):
    """启动简化工作流"""
    if project_id in active_workflows:
        logger.warning(f"Workflow already running for project {project_id}")
        return None
    
    # 创建线程运行工作流
    def run_workflow():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_execute_full_workflow(project_id, config))
        except Exception as e:
            logger.error(f"Workflow failed for project {project_id}: {e}")
        finally:
            # 清理
            if project_id in active_workflows:
                del active_workflows[project_id]
            loop.close()
    
    thread = threading.Thread(target=run_workflow, daemon=True)
    thread.start()
    active_workflows[project_id] = thread
    
    logger.info(f"Simple workflow started for project {project_id}")
    return thread


def cancel_simple_workflow(project_id: int):
    """取消简化工作流"""
    if project_id in active_workflows:
        # 注意：Python 线程不能直接取消，我们只能更新状态
        logger.warning(f"Cannot force cancel thread for project {project_id}")
        
        # 更新状态
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = "failed"
            db.commit()
        finally:
            db.close()
        
        # 清理
        del active_workflows[project_id]
        
        return True
    
    return False


def is_workflow_running(project_id: int) -> bool:
    """检查工作流是否正在运行"""
    return project_id in active_workflows and active_workflows[project_id].is_alive()
