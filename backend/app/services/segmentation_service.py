"""
智能分段服务
"""
import re
from typing import List, Dict, Any, Optional


class SegmentationService:
    """智能分段服务类"""
    
    # 默认分段参数
    DEFAULT_MIN_LENGTH = 50
    DEFAULT_MAX_LENGTH = 500
    
    # 章节标题匹配模式
    CHAPTER_PATTERNS = [
        r'^第[一二三四五六七八九十百千万]+[章节卷集篇].*$',
        r'^第\s*\d+\s*[章节卷集篇].*$',
        r'^\d+\..*$',
        r'^[一二三四五六七八九十]+、.*$',
    ]
    
    @staticmethod
    def is_chapter_title(line: str) -> bool:
        """判断一行是否是章节标题"""
        line = line.strip()
        if not line:
            return False
        
        for pattern in SegmentationService.CHAPTER_PATTERNS:
            if re.match(pattern, line, re.UNICODE):
                return True
        return False
    
    @staticmethod
    def segment(
        text: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        detect_chapters: bool = True
    ) -> List[Dict[str, Any]]:
        """
        将文本智能分段
        
        Args:
            text: 输入文本
            min_length: 段落最小长度
            max_length: 段落最大长度
            detect_chapters: 是否检测章节标题
            
        Returns:
            分段结果列表
        """
        min_len = min_length or SegmentationService.DEFAULT_MIN_LENGTH
        max_len = max_length or SegmentationService.DEFAULT_MAX_LENGTH
        
        # 按行分割
        lines = text.split('\n')
        
        segments: List[Dict[str, Any]] = []
        current_segment: List[str] = []
        current_length = 0
        current_chapter = None
        
        for line in lines:
            stripped_line = line.strip()
            
            # 检测章节标题
            if detect_chapters and SegmentationService.is_chapter_title(stripped_line):
                # 如果有未完成的段落，先保存
                if current_segment:
                    segments.append(SegmentationService._create_segment(
                        current_segment, len(segments), current_chapter
                    ))
                    current_segment = []
                    current_length = 0
                
                current_chapter = stripped_line
                continue
            
            # 如果当前段落为空且当前行为空，跳过
            if not current_segment and not stripped_line:
                continue
            
            # 计算加入当前行后的长度
            new_length = current_length + len(stripped_line) + 1  # +1 是换行符
            
            # 如果超过最大长度且当前段落不为空，先保存
            if current_segment and new_length > max_len:
                segments.append(SegmentationService._create_segment(
                    current_segment, len(segments), current_chapter
                ))
                current_segment = []
                current_length = 0
            
            # 加入当前行
            current_segment.append(line)
            current_length += len(line) + 1
        
        # 保存最后一段
        if current_segment:
            segments.append(SegmentationService._create_segment(
                current_segment, len(segments), current_chapter
            ))
        
        # 后处理：合并过短的段落
        segments = SegmentationService._merge_short_segments(segments, min_len)
        
        return segments
    
    @staticmethod
    def _create_segment(
        lines: List[str],
        index: int,
        chapter_title: Optional[str]
    ) -> Dict[str, Any]:
        """创建一个段落实体"""
        text = '\n'.join(lines).strip()
        return {
            "index": index,
            "text": text,
            "char_count": len(text),
            "chapter_title": chapter_title
        }
    
    @staticmethod
    def _merge_short_segments(
        segments: List[Dict[str, Any]],
        min_length: int
    ) -> List[Dict[str, Any]]:
        """合并过短的段落"""
        if len(segments) <= 1:
            return segments
        
        result: List[Dict[str, Any]] = []
        buffer: List[Dict[str, Any]] = []
        
        for seg in segments:
            buffer.append(seg)
            
            # 计算缓冲区内的总字符数
            total_length = sum(s['char_count'] for s in buffer)
            
            if total_length >= min_length:
                # 合并缓冲区
                merged = SegmentationService._merge_segment_list(buffer)
                result.append(merged)
                buffer = []
        
        # 处理剩余的缓冲内容
        if buffer:
            if result:
                # 合并到最后一段
                result[-1] = SegmentationService._merge_segment_list(
                    [result[-1]] + buffer
                )
            else:
                result.extend(buffer)
        
        # 重新编号
        for i, seg in enumerate(result):
            seg['index'] = i
        
        return result
    
    @staticmethod
    def _merge_segment_list(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个段落实体"""
        if not segments:
            raise ValueError("段列表不能为空")
        
        if len(segments) == 1:
            return segments[0]
        
        # 合并文本
        merged_text = '\n'.join(s['text'] for s in segments)
        
        # 使用第一个段落的章节标题
        chapter_title = None
        for seg in segments:
            if seg.get('chapter_title'):
                chapter_title = seg['chapter_title']
                break
        
        return {
            "index": segments[0]['index'],
            "text": merged_text,
            "char_count": len(merged_text),
            "chapter_title": chapter_title
        }
