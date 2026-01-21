# app/services/file_processor.py
"""
文件处理服务：负责各种格式文件的文本提取和分块
"""
import os
import logging
from typing import List, Tuple, Dict, Any
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class FileProcessor:
    """文件处理器"""

    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS

        logger.info(f"初始化文件处理器: chunk_size={self.chunk_size}, "
                    f"chunk_overlap={self.chunk_overlap}")

    def is_file_allowed(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.allowed_extensions

    def process_file(self, file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        处理文件，提取文本并分块

        Args:
            file_path: 文件路径

        Returns:
            Tuple[List[str], List[Dict[str, Any]]]: (文本块列表, 元数据列表)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_ext = Path(file_path).suffix.lower()

        # 根据文件类型选择处理方法
        if file_ext == '.pdf':
            return self._process_pdf(file_path)
        elif file_ext == '.txt' or file_ext == '.md':
            return self._process_text(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self._process_docx(file_path)
        else:
            # 对于其他格式，先使用文本处理方法
            logger.warning(f"未实现 {file_ext} 格式的专用处理器，使用通用文本处理")
            return self._process_text(file_path)

    def _process_text(self, file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """处理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                logger.warning(f"文件内容为空: {file_path}")
                return [], []

            # 简单的分块逻辑（后续可以替换为更智能的分块）
            chunks = self._simple_text_chunking(content)

            # 生成元数据
            metadatas = []
            for i, chunk in enumerate(chunks):
                metadatas.append({
                    "source": os.path.basename(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_type": "text"
                })

            logger.info(f"文本文件处理完成: {file_path}, 分块数: {len(chunks)}")
            return chunks, metadatas

        except Exception as e:
            logger.error(f"处理文本文件失败 {file_path}: {e}")
            raise

    def _process_pdf(self, file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """处理PDF文件"""
        try:
            # 先实现简单版本，稍后添加PyPDF2
            logger.warning(f"PDF处理尚未实现: {file_path}")

            # 临时返回空结果
            chunks = ["PDF处理功能待实现"]
            metadatas = [{
                "source": os.path.basename(file_path),
                "chunk_index": 0,
                "total_chunks": 1,
                "file_type": "pdf",
                "note": "PDF处理功能待实现"
            }]

            return chunks, metadatas

        except Exception as e:
            logger.error(f"处理PDF文件失败 {file_path}: {e}")
            raise

    def _process_docx(self, file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """处理Word文档"""
        try:
            # 先实现简单版本，稍后添加python-docx
            logger.warning(f"Word文档处理尚未实现: {file_path}")

            # 临时返回空结果
            chunks = ["Word文档处理功能待实现"]
            metadatas = [{
                "source": os.path.basename(file_path),
                "chunk_index": 0,
                "total_chunks": 1,
                "file_type": "docx",
                "note": "Word文档处理功能待实现"
            }]

            return chunks, metadatas

        except Exception as e:
            logger.error(f"处理Word文档失败 {file_path}: {e}")
            raise

    def _simple_text_chunking(self, text: str) -> List[str]:
        """简单的文本分块算法"""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # 计算块结束位置
            end = min(start + self.chunk_size, text_length)

            # 如果不在文本末尾，尝试在句子边界处结束
            if end < text_length:
                # 查找最近的句子结束符
                sentence_ends = ['.', '!', '?', '。', '！', '？', '\n\n']
                for i in range(end, start, -1):
                    if text[i - 1] in sentence_ends and (i - start) > self.chunk_size * 0.7:
                        end = i
                        break

            # 提取块
            chunk = text[start:end].strip()
            if chunk:  # 只添加非空块
                chunks.append(chunk)

            # 移动起始位置，考虑重叠
            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        stat = os.stat(file_path)
        return {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": stat.st_size,
            "file_type": Path(file_path).suffix.lower(),
            "modified_time": stat.st_mtime,
            "created_time": stat.st_ctime
        }


# 创建全局实例
file_processor = FileProcessor()