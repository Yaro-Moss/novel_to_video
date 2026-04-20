"""
字幕生成服务
"""
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False


class SubtitleService:
    """字幕生成服务"""
    
    @staticmethod
    def generate_srt_from_segments(
        segments: List[Dict[str, Any]],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        从段落列表生成 SRT 字幕
        
        Args:
            segments: 段落列表，每个段落需要包含：
                     - text: 文本内容
                     - start_time: 开始时间
                     - end_time: 结束时间
                     - index: 序号（可选）
            output_path: 输出文件路径
            
        Returns:
            包含字幕信息的字典
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments):
                index = segment.get('index', i + 1)
                text = segment.get('text', '')
                start_time = segment.get('start_time', 0.0)
                end_time = segment.get('end_time', 0.0)
                
                # 格式化时间为 SRT 格式: 00:00:00,000
                start_str = SubtitleService._format_time_srt(start_time)
                end_str = SubtitleService._format_time_srt(end_time)
                
                f.write(f"{index}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{text}\n\n")
        
        return {
            "success": True,
            "file_path": str(output_path),
            "segment_count": len(segments)
        }
    
    @staticmethod
    def generate_simple_srt(
        text: str,
        duration: float,
        output_path: Path,
        max_chars_per_line: int = 40
    ) -> Dict[str, Any]:
        """
        为单段文本生成简单的 SRT 字幕
        
        Args:
            text: 文本内容
            duration: 总时长（秒）
            output_path: 输出文件路径
            max_chars_per_line: 每行最大字符数
            
        Returns:
            生成结果
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 分割长文本
        lines = []
        while len(text) > max_chars_per_line:
            split_pos = text.rfind(' ', 0, max_chars_per_line)
            if split_pos == -1:
                split_pos = max_chars_per_line
            lines.append(text[:split_pos])
            text = text[split_pos:].lstrip()
        if text:
            lines.append(text)
        
        # 生成字幕
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("1\n")
            f.write(f"00:00:00,000 --> {SubtitleService._format_time_srt(duration)}\n")
            f.write("\n".join(lines))
            f.write("\n\n")
        
        return {
            "success": True,
            "file_path": str(output_path)
        }
    
    @staticmethod
    def _format_time_srt(seconds: float) -> str:
        """
        将秒数转换为 SRT 时间格式
        
        Args:
            seconds: 秒数
            
        Returns:
            SRT 格式的时间字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    @staticmethod
    def burn_subtitles_to_video(
        video_path: Path,
        subtitle_path: Path,
        output_path: Path,
        font_name: str = "Arial",
        font_size: int = 24,
        font_color: str = "white",
        position: str = "bottom",
        border_color: str = "black",
        border_width: int = 2
    ) -> Dict[str, Any]:
        """
        将字幕烧录到视频中
        
        Args:
            video_path: 输入视频路径
            subtitle_path: 字幕文件路径
            output_path: 输出视频路径
            font_name: 字体名称
            font_size: 字体大小
            font_color: 字体颜色
            position: 位置 ("top", "center", "bottom")
            border_color: 边框颜色
            border_width: 边框宽度
            
        Returns:
            处理结果
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        input_video = ffmpeg.input(str(video_path))
        
        # 设置字幕滤镜选项
        subtitles_options = {
            'force_style': (
                f"FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour={SubtitleService._color_to_ass(font_color)},"
                f"OutlineColour={SubtitleService._color_to_ass(border_color)},"
                f"Outline={border_width}"
            )
        }
        
        # 应用字幕滤镜
        v = input_video.video.filter('subtitles', str(subtitle_path), **subtitles_options)
        a = input_video.audio
        
        # 输出视频
        out = ffmpeg.output(
            v, a,
            str(output_path),
            vcodec='libx264',
            acodec='aac',
            crf=23
        )
        
        ffmpeg.run(out, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        return {
            "success": True,
            "file_path": str(output_path)
        }
    
    @staticmethod
    def _color_to_ass(color_name: str) -> str:
        """
        将颜色名称转换为 ASS 格式 (BBGGRR)
        
        Args:
            color_name: 颜色名称或 hex
            
        Returns:
            ASS 格式的颜色
        """
        color_map = {
            "white": "&H00FFFFFF",
            "black": "&H00000000",
            "red": "&H000000FF",
            "green": "&H0000FF00",
            "blue": "&H00FF0000",
            "yellow": "&H0000FFFF"
        }
        
        return color_map.get(color_name.lower(), "&H00FFFFFF")
    
    @staticmethod
    def get_available_fonts() -> list:
        """获取可用字体（简化版）"""
        return [
            "Arial",
            "Microsoft YaHei",
            "SimHei",
            "SimSun"
        ]
    
    @staticmethod
    def get_available_positions() -> list:
        """获取可用的字幕位置"""
        return [
            {"id": "top", "name": "顶部"},
            {"id": "center", "name": "中间"},
            {"id": "bottom", "name": "底部"}
        ]
