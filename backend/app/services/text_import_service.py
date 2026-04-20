"""
文本导入服务
"""
import os
import chardet
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings, BASE_DIR

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class TextImportService:
    """文本导入服务类"""
    
    @staticmethod
    def _read_txt(file_path: Path) -> str:
        """读取TXT文件"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # 检测编码
        detection = chardet.detect(raw_data)
        encoding = detection.get('encoding', 'utf-8')
        
        # 尝试使用检测到的编码读取
        try:
            return raw_data.decode(encoding)
        except (UnicodeDecodeError, TypeError):
            # 如果失败，尝试其他常见编码
            fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1']
            for enc in fallback_encodings:
                try:
                    return raw_data.decode(enc)
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"无法解码文件: {file_path}")
    
    @staticmethod
    def _read_pdf(file_path: Path) -> str:
        """读取PDF文件"""
        if PdfReader is None:
            raise ImportError("PyPDF2库未安装，无法读取PDF文件")
        
        text_parts = []
        reader = PdfReader(str(file_path))
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return '\n'.join(text_parts)
    
    @staticmethod
    def _read_docx(file_path: Path) -> str:
        """读取Word文档"""
        if Document is None:
            raise ImportError("python-docx库未安装，无法读取Word文档")
        
        doc = Document(str(file_path))
        text_parts = []
        
        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)
        
        return '\n'.join(text_parts)
    
    @staticmethod
    def read_file(file_path: str) -> Dict[str, Any]:
        """
        读取文件，支持TXT、PDF、DOCX格式
        
        Args:
            file_path: 文件的相对路径（相对于项目根目录）
            
        Returns:
            包含文本内容和元信息的字典
        """
        full_path = BASE_DIR / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 根据文件扩展名选择读取方式
        ext = full_path.suffix.lower()
        
        if ext == '.pdf':
            content = TextImportService._read_pdf(full_path)
        elif ext == '.docx':
            content = TextImportService._read_docx(full_path)
        elif ext == '.txt':
            content = TextImportService._read_txt(full_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        # 计算字符数（去除首尾空白）
        cleaned_content = content.strip()
        char_count = len(cleaned_content)
        
        return {
            "content": content,
            "cleaned_content": cleaned_content,
            "file_format": ext.lstrip('.'),
            "char_count": char_count,
            "file_size": os.path.getsize(full_path),
            "file_path": file_path
        }
