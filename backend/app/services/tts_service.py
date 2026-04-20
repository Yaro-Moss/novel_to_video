"""
TTS 服务 - 支持 Edge TTS 和 Kokoro TTS
"""
import asyncio
import edge_tts
import os
import struct
import wave
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 尝试导入 Kokoro TTS
try:
    from kokoro_onnx import Kokoro
    import soundfile as sf
    KOKORO_AVAILABLE = True
except ImportError as e:
    KOKORO_AVAILABLE = False
    logger.warning(f"Kokoro TTS not available: {e}, using Edge TTS only")


class TTSService:
    """TTS 服务类 - 支持多种 TTS 引擎"""
    
    # TTS 引擎类型
    TTS_ENGINE_EDGE = "edge"
    TTS_ENGINE_KOKORO = "kokoro"
    
    # 常用语音列表 (Edge TTS)
    DEFAULT_VOICES_EDGE = {
        "zh-CN-XiaoxiaoNeural": {"gender": "Female", "language": "zh-CN", "name": "晓晓"},
        "zh-CN-YunxiNeural": {"gender": "Male", "language": "zh-CN", "name": "云希"},
        "zh-CN-YunjianNeural": {"gender": "Male", "language": "zh-CN", "name": "云健"},
        "zh-CN-XiaoyiNeural": {"gender": "Female", "language": "zh-CN", "name": "晓伊"},
    }
    
    # Kokoro TTS 语音列表 (中文友好)
    DEFAULT_VOICES_KOKORO = {
        "af_heart": {"gender": "Female", "language": "zh-CN", "name": "Kokoro 女声1"},
        "af_bella": {"gender": "Female", "language": "zh-CN", "name": "Kokoro 女声2"},
        "am_adam": {"gender": "Male", "language": "zh-CN", "name": "Kokoro 男声1"},
        "am_michael": {"gender": "Male", "language": "zh-CN", "name": "Kokoro 男声2"},
    }
    
    # Kokoro 模型实例 (懒加载)
    _kokoro_model = None
    
    @staticmethod
    async def get_voices(engine: str = TTS_ENGINE_EDGE) -> List[Dict[str, Any]]:
        """
        获取可用语音列表
        
        Args:
            engine: TTS 引擎类型 ("edge" 或 "kokoro")
        
        Returns:
            语音列表
        """
        if engine == TTSService.TTS_ENGINE_KOKORO and KOKORO_AVAILABLE:
            try:
                # 返回 Kokoro 的默认语音
                return [
                    {
                        "id": k,
                        "name": v["name"],
                        "gender": v["gender"],
                        "language": v["language"],
                        "preview": None
                    }
                    for k, v in TTSService.DEFAULT_VOICES_KOKORO.items()
                ]
            except Exception as e:
                logger.warning(f"Failed to get Kokoro voices, falling back to Edge: {e}")
        
        # 默认使用 Edge TTS
        try:
            voices = await edge_tts.list_voices()
            
            # 格式化返回结果
            result = []
            for voice in voices:
                result.append({
                    "id": voice["Name"],
                    "name": voice["FriendlyName"],
                    "gender": voice["Gender"],
                    "language": voice["Locale"],
                    "preview": None  # 可添加预览功能
                })
            
            return result
        except Exception as e:
            logger.warning(f"Failed to get voices list, using defaults: {e}")
            # 如果获取失败，返回默认语音列表
            return [
                {
                    "id": k,
                    "name": v["name"],
                    "gender": v["gender"],
                    "language": v["language"],
                    "preview": None
                }
                for k, v in TTSService.DEFAULT_VOICES_EDGE.items()
            ]
    
    @staticmethod
    def _generate_silent_audio(duration_seconds: float = 1.0) -> bytes:
        """
        生成静默音频作为fallback
        
        Args:
            duration_seconds: 音频时长（秒）
            
        Returns:
            WAV格式的音频数据
        """
        sample_rate = 16000
        num_channels = 1
        sample_width = 2
        num_frames = int(sample_rate * duration_seconds)
        
        # 创建内存中的WAV文件
        import io
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            
            # 生成静默数据（全零）
            silent_data = b'\x00\x00' * num_frames
            wav_file.writeframes(silent_data)
        
        buffer.seek(0)
        return buffer.read()
    
    @staticmethod
    def _load_kokoro_model():
        """懒加载 Kokoro 模型"""
        if TTSService._kokoro_model is None and KOKORO_AVAILABLE:
            try:
                logger.info("Loading Kokoro TTS model...")
                # 模型文件会在当前目录或默认位置查找
                model_path = settings.model_dir_path / "kokoro-v1.0.onnx"
                voices_path = settings.model_dir_path / "voices-v1.0.bin"
                try:
                    TTSService._kokoro_model = Kokoro(str(model_path), str(voices_path))
                except FileNotFoundError:
                    # 如果找不到，尝试当前目录或让库自动下载
                    try:
                        TTSService._kokoro_model = Kokoro()
                    except Exception as e2:
                        logger.warning(f"Could not load with default paths: {e2}")
                        logger.warning("Falling back to Edge TTS for now")
                        raise
                logger.info("Kokoro TTS model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Kokoro model: {e}")
                raise
        return TTSService._kokoro_model
    
    @staticmethod
    async def _synthesize_kokoro(
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0
    ) -> bytes:
        """
        使用 Kokoro TTS 合成语音
        
        Args:
            text: 要合成的文本
            voice: 语音ID
            speed: 语速 (0.5-2.0)
            
        Returns:
            WAV 格式音频数据
        """
        if not KOKORO_AVAILABLE:
            raise RuntimeError("Kokoro TTS not available")
        
        loop = asyncio.get_event_loop()
        
        # 在线程池中执行同步操作
        def _sync_synthesize():
            model = TTSService._load_kokoro_model()
            # 使用 create 方法，并指定语言为中文
            audio_samples, sample_rate = model.create(
                text, 
                voice=voice, 
                speed=speed, 
                lang="zh-cn"
            )
            
            # 转换为 WAV 格式
            buffer = io.BytesIO()
            sf.write(buffer, audio_samples, sample_rate, format='WAV')
            buffer.seek(0)
            return buffer.read()
        
        return await loop.run_in_executor(None, _sync_synthesize)
    
    @staticmethod
    async def synthesize(
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = TTS_ENGINE_EDGE
    ) -> bytes:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice: 语音ID
            rate: 语速 (Edge TTS 使用)
            volume: 音量 (Edge TTS 使用)
            pitch: 音调 (Edge TTS 使用)
            engine: TTS 引擎类型 ("edge" 或 "kokoro")
            
        Returns:
            音频数据
        """
        try:
            # 尝试使用指定的引擎
            if engine == TTSService.TTS_ENGINE_KOKORO and KOKORO_AVAILABLE:
                try:
                    # 转换 rate 字符串为 float (Kokoro 的 speed 参数)
                    speed = 1.0
                    if rate.startswith("+"):
                        speed = 1.0 + int(rate.replace("%", "")) / 100.0
                    elif rate.startswith("-"):
                        speed = 1.0 - int(rate.replace("%", "")) / 100.0
                    
                    return await TTSService._synthesize_kokoro(text, voice, speed)
                except Exception as e:
                    logger.warning(f"Kokoro TTS failed, falling back to Edge: {e}")
            
            # 默认使用 Edge TTS
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            
            if len(audio_data) > 0:
                return bytes(audio_data)
            else:
                raise ValueError("No audio data received")
                
        except Exception as e:
            logger.warning(f"TTS synthesis failed, using silent fallback: {e}")
            # 计算大概需要的音频时长（每个中文字符约0.2秒）
            estimated_duration = max(1.0, len(text) * 0.2)
            return TTSService._generate_silent_audio(estimated_duration)
    
    @staticmethod
    async def synthesize_to_file(
        text: str,
        output_path: Path,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = TTS_ENGINE_EDGE
    ) -> Dict[str, Any]:
        """
        合成语音并保存到文件
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            voice: 语音ID
            rate: 语速
            volume: 音量
            pitch: 音调
            engine: TTS 引擎类型 ("edge" 或 "kokoro")
            
        Returns:
            包含文件信息的字典
        """
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 合成音频
        audio_data = await TTSService.synthesize(
            text, voice, rate, volume, pitch, engine
        )
        
        # 保存到文件
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        return {
            "success": True,
            "file_path": str(output_path),
            "file_size": len(audio_data),
            "char_count": len(text),
            "engine": engine
        }
    
    @staticmethod
    async def synthesize_batch(
        segments: List[Dict[str, Any]],
        output_dir: Path,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = TTS_ENGINE_EDGE,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        批量合成语音
        
        Args:
            segments: 段落列表
            output_dir: 输出目录
            voice: 语音ID
            rate: 语速
            volume: 音量
            pitch: 音调
            progress_callback: 进度回调函数
            
        Returns:
            合成结果列表
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        total = len(segments)
        
        for i, segment in enumerate(segments):
            try:
                text = segment.get('text', '')
                if not text.strip():
                    continue
                
                # Kokoro 生成 WAV，Edge TTS 生成 MP3
                ext = "wav" if engine == TTSService.TTS_ENGINE_KOKORO else "mp3"
                output_file = output_dir / f"segment_{i}.{ext}"
                
                result = await TTSService.synthesize_to_file(
                    text,
                    output_file,
                    voice,
                    rate,
                    volume,
                    pitch,
                    engine
                )
                
                result["segment_index"] = i
                results.append(result)
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(i + 1, total, segment)
                    
            except Exception as e:
                results.append({
                    "success": False,
                    "segment_index": i,
                    "error": str(e)
                })
        
        return results
