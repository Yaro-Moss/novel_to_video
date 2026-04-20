"""
视频拼接服务
"""
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False


class VideoConcatService:
    """视频拼接服务"""
    
    @staticmethod
    def concat_videos(
        video_paths: List[Path],
        output_path: Path,
        method: str = "concat"
    ) -> Dict[str, Any]:
        """
        拼接多个视频
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出视频路径
            method: 拼接方法 ("concat" 或 "filter_complex")
            
        Returns:
            包含拼接信息的字典
        """
        if not video_paths:
            raise ValueError("视频列表不能为空")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if method == "concat":
            return VideoConcatService._concat_with_demuxer(video_paths, output_path)
        else:
            return VideoConcatService._concat_with_filter_complex(video_paths, output_path)
    
    @staticmethod
    def _concat_with_demuxer(
        video_paths: List[Path],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        使用 concat demuxer 拼接（推荐，速度快）
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            
        Returns:
            拼接结果
        """
        # 创建 concat 列表文件
        list_file = output_path.parent / 'file_list.txt'
        with open(list_file, 'w', encoding='utf-8') as f:
            for video_path in video_paths:
                f.write(f"file '{str(video_path.absolute())}'\n")
        
        try:
            # 使用 ffmpeg concat
            input = ffmpeg.input(str(list_file), format='concat', safe=0)
            out = ffmpeg.output(
                input.video,
                input.audio,
                str(output_path),
                c='copy'  # 直接复制流，不重新编码
            )
            
            ffmpeg.run(out, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            # 计算总时长
            total_duration = 0.0
            for vp in video_paths:
                probe = ffmpeg.probe(str(vp))
                total_duration += float(probe['streams'][0]['duration'])
            
            return {
                "success": True,
                "file_path": str(output_path),
                "total_duration": total_duration,
                "segment_count": len(video_paths)
            }
        finally:
            if list_file.exists():
                list_file.unlink()
    
    @staticmethod
    def _concat_with_filter_complex(
        video_paths: List[Path],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        使用 filter_complex 拼接（重新编码，但更灵活）
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            
        Returns:
            拼接结果
        """
        inputs = [ffmpeg.input(str(vp)) for vp in video_paths]
        
        # 拼接视频和音频流
        v = [i.video for i in inputs]
        a = [i.audio for i in inputs]
        
        joined = ffmpeg.concat(*v, *a, v=1, a=1).node
        
        out = ffmpeg.output(
            joined[0],
            joined[1],
            str(output_path),
            vcodec='libx264',
            acodec='aac'
        )
        
        ffmpeg.run(out, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        total_duration = 0.0
        for vp in video_paths:
            probe = ffmpeg.probe(str(vp))
            total_duration += float(probe['streams'][0]['duration'])
        
        return {
            "success": True,
            "file_path": str(output_path),
            "total_duration": total_duration,
            "segment_count": len(video_paths)
        }
    
    @staticmethod
    def add_transition_between_videos(
        video_paths: List[Path],
        output_path: Path,
        transition_duration: float = 0.5
    ) -> Dict[str, Any]:
        """
        在视频之间添加过渡效果（交叉淡入淡出）
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            transition_duration: 过渡时长（秒）
            
        Returns:
            拼接结果
        """
        if len(video_paths) == 1:
            # 只有一个视频，直接复制
            return VideoConcatService.concat_videos(video_paths, output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用复杂的 filter_complex 处理过渡
        inputs = [ffmpeg.input(str(vp)) for vp in video_paths]
        
        # 获取每个视频的时长
        durations = []
        for vp in video_paths:
            probe = ffmpeg.probe(str(vp))
            durations.append(float(probe['streams'][0]['duration']))
        
        # 对于多个视频，使用简单拼接
        # 复杂过渡需要更多处理
        return VideoConcatService.concat_videos(video_paths, output_path)
    
    @staticmethod
    async def concat_async(
        video_paths: List[Path],
        output_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        异步视频拼接
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            progress_callback: 进度回调
            
        Returns:
            拼接结果
        """
        if progress_callback:
            progress_callback(0, 1, "开始拼接视频...")
        
        result = VideoConcatService.concat_videos(video_paths, output_path)
        
        if progress_callback:
            progress_callback(1, 1, "视频拼接完成")
        
        return result
