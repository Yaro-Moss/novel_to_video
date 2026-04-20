"""
视频段合成服务
"""
from pathlib import Path
from typing import Dict, Any, Optional
import math

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False


class VideoSegmentService:
    """视频段合成服务"""
    
    @staticmethod
    def create_segment(
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        fade_in: float = 0.5,
        fade_out: float = 0.5,
        transition: str = "crossfade"
    ) -> Dict[str, Any]:
        """
        合成单个视频段（图片 + 音频）
        
        Args:
            image_path: 图片路径
            audio_path: 音频路径
            output_path: 输出视频路径
            fade_in: 淡入时长（秒）
            fade_out: 淡出时长（秒）
            transition: 过渡效果
            
        Returns:
            包含视频信息的字典
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 先获取音频时长
        probe = ffmpeg.probe(str(audio_path))
        audio_duration = float(probe['streams'][0]['duration'])
        
        # 使用 ffmpeg 合成
        input_image = ffmpeg.input(str(image_path), loop=1, framerate=24, t=audio_duration)
        input_audio = ffmpeg.input(str(audio_path))
        
        # 添加淡入淡出效果
        v = input_image.video
        a = input_audio.audio
        
        if fade_in > 0:
            v = v.filter('fade', type='in', start_time=0, duration=fade_in)
            a = a.filter('afade', type='in', start_time=0, duration=fade_in)
        
        if fade_out > 0:
            v = v.filter('fade', type='out', start_time=audio_duration - fade_out, duration=fade_out)
            a = a.filter('afade', type='out', start_time=audio_duration - fade_out, duration=fade_out)
        
        # 输出视频
        out = ffmpeg.output(
            v, a,
            str(output_path),
            vcodec='libx264',
            acodec='aac',
            pix_fmt='yuv420p',
            r=24,
            crf=23,
            shortest=None
        )
        
        ffmpeg.run(out, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        return {
            "success": True,
            "file_path": str(output_path),
            "duration": audio_duration,
            "image_path": str(image_path),
            "audio_path": str(audio_path)
        }
    
    @staticmethod
    def create_from_memory(
        image_data: bytes,
        audio_data: bytes,
        output_path: Path,
        temp_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        从内存中的数据创建视频段
        
        Args:
            image_data: 图片二进制数据
            audio_data: 音频二进制数据
            output_path: 输出路径
            temp_dir: 临时目录
            
        Returns:
            合成结果
        """
        temp_dir = temp_dir or Path('/tmp') / 'video_temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存临时文件
        temp_image = temp_dir / 'temp_image.png'
        temp_audio = temp_dir / 'temp_audio.mp3'
        
        with open(temp_image, 'wb') as f:
            f.write(image_data)
        
        with open(temp_audio, 'wb') as f:
            f.write(audio_data)
        
        try:
            result = VideoSegmentService.create_segment(
                temp_image, temp_audio, output_path
            )
            return result
        finally:
            # 清理临时文件
            if temp_image.exists():
                temp_image.unlink()
            if temp_audio.exists():
                temp_audio.unlink()
    
    @staticmethod
    async def create_segment_async(
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        异步版本的视频段合成（可以调用进度回调）
        
        Args:
            image_path: 图片路径
            audio_path: 音频路径
            output_path: 输出路径
            progress_callback: 进度回调函数
            
        Returns:
            合成结果
        """
        if progress_callback:
            progress_callback(0, 1, "开始合成视频段...")
        
        result = VideoSegmentService.create_segment(
            image_path, audio_path, output_path
        )
        
        if progress_callback:
            progress_callback(1, 1, "视频段合成完成")
        
        return result
