# app/services/document_service.py
"""
文档服务：负责文档的CRUD和向量化处理
"""
import os
import uuid
import shutil
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.services.file_processor import file_processor
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)


class DocumentService:
    """文档服务"""

    def __init__(self):
        self.upload_dir = settings.upload_path
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"文档服务初始化，上传目录: {self.upload_dir}")

    async def save_uploaded_file(self, file: UploadFile) -> str:
        """
        保存上传的文件到服务器
        
        Args:
            file: FastAPI的UploadFile对象
            
        Returns:
            str: 保存后的文件路径
        """
        try:
            # 生成唯一文件名（使用UUID避免冲突）
            file_ext = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_dir, unique_filename)

            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(f"文件保存成功: {file.filename} -> {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise

    def process_document_background(self, document_id: int, db_session: Session):
        """
        后台处理文档（用于 BackgroundTasks）
        
        Args:
            document_id: 文档ID
            db_session: 数据库会话（注意：需要新的会话）
        """
        try:
            logger.info(f"开始后台处理文档: ID={document_id}")
            
            # 创建新的数据库会话（后台任务需要独立会话）
            from app.database import SessionLocal
            db = SessionLocal()
            
            try:
                document, chunks_count = self.process_document(
                    db=db,
                    document_id=document_id,
                    process_content=True
                )
                logger.info(f"文档处理完成: ID={document_id}, 分块数={chunks_count}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"后台处理文档失败 (ID={document_id}): {e}", exc_info=True)

    def create_document_record(
            self,
            db: Session,
            filename: str,
            file_path: str,
            file_size: int,
            user_id: Optional[str] = None
    ) -> Document:
        """创建文档记录（不处理内容）"""
        try:
            file_ext = Path(filename).suffix.lower()

            document = Document(
                filename=filename,
                file_path=file_path,
                file_type=file_ext,
                file_size=file_size,
                user_id=user_id,
                file_metadata={
                    "original_filename": filename,
                    "upload_time": datetime.utcnow().isoformat(),
                    "status": "pending"  # 待处理
                }
            )

            db.add(document)
            db.commit()
            db.refresh(document)

            logger.info(f"创建文档记录成功: ID={document.id}, 文件名={filename}")

            return document

        except Exception as e:
            db.rollback()
            logger.error(f"创建文档记录失败: {e}")
            raise

    def process_document(
            self,
            db: Session,
            document_id: int,
            process_content: bool = True
    ) -> Tuple[Document, int]:
        """
        处理文档内容（文本提取、分块、向量化）

        Args:
            db: 数据库会话
            document_id: 文档ID
            process_content: 是否处理内容（向量化）

        Returns:
            Tuple[Document, int]: (文档对象, 处理的分块数)
        """
        try:
            # 获取文档
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"文档不存在: ID={document_id}")

            # 检查文件是否存在
            if not os.path.exists(document.file_path):
                raise FileNotFoundError(f"文件不存在: {document.file_path}")

            logger.info(f"开始处理文档: ID={document_id}, 文件={document.filename}")

            # 更新状态
            document.file_metadata["status"] = "processing"
            document.file_metadata["process_start_time"] = datetime.utcnow().isoformat()
            db.commit()

            # 1. 提取文本并分块
            chunks, metadatas = file_processor.process_file(document.file_path)

            if not chunks:
                logger.warning(f"文档内容为空或无文本: {document.filename}")

                # 更新状态
                document.file_metadata["status"] = "completed"
                document.file_metadata["process_end_time"] = datetime.utcnow().isoformat()
                document.file_metadata["chunks_count"] = 0
                db.commit()

                return document, 0

            # 2. 向量化（如果启用）
            embeddings = None
            if process_content:
                logger.info(f"生成向量嵌入: {len(chunks)} 个块")
                embeddings = vector_service.get_embeddings_batch(chunks)

            # 3. 保存文档块到数据库
            saved_chunks = 0
            for i, (chunk_text, metadata) in enumerate(zip(chunks, metadatas)):
                try:
                    # 准备块数据
                    chunk_data = {
                        "document_id": document.id,
                        "chunk_index": i,
                        "chunk_text": chunk_text,
                        "chunk_metadata": metadata
                    }

                    # 添加向量（如果有）
                    if embeddings and i < len(embeddings):
                        chunk_data["embedding"] = embeddings[i]

                    # 创建文档块
                    document_chunk = DocumentChunk(**chunk_data)
                    db.add(document_chunk)
                    saved_chunks += 1

                except Exception as e:
                    logger.error(f"保存文档块失败 (索引={i}): {e}")

            # 批量提交
            db.commit()

            # 4. 更新文档状态
            document.file_metadata["status"] = "completed"
            document.file_metadata["process_end_time"] = datetime.utcnow().isoformat()
            document.file_metadata["chunks_count"] = saved_chunks
            db.commit()

            logger.info(f"文档处理完成: ID={document_id}, 保存块数={saved_chunks}")

            return document, saved_chunks

        except Exception as e:
            # 更新状态为失败
            try:
                document.file_metadata["status"] = "failed"
                document.file_metadata["error"] = str(e)
                db.commit()
            except:
                pass

            logger.error(f"处理文档失败 (ID={document_id}): {e}")
            raise

    def upload_and_process(
            self,
            db: Session,
            file_content: bytes,
            filename: str,
            user_id: Optional[str] = None
    ) -> Document:
        """
        上传文件并处理

        Args:
            db: 数据库会话
            file_content: 文件内容（字节）
            filename: 文件名
            user_id: 用户ID

        Returns:
            Document: 创建的文档对象
        """
        try:
            # 1. 验证文件类型
            if not file_processor.is_file_allowed(filename):
                raise ValueError(f"不支持的文件类型: {filename}")

            # 2. 验证文件大小
            file_size = len(file_content)
            if file_size > settings.MAX_FILE_SIZE:
                raise ValueError(f"文件太大: {file_size}字节，最大允许{settings.MAX_FILE_SIZE}字节")

            # 3. 保存文件
            safe_filename = self._get_safe_filename(filename)
            file_path = os.path.join(self.upload_dir, safe_filename)

            # 确保上传目录存在
            os.makedirs(self.upload_dir, exist_ok=True)

            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(file_content)

            logger.info(f"文件保存成功: {file_path} ({file_size}字节)")

            # 4. 创建文档记录
            document = self.create_document_record(
                db, filename, file_path, file_size, user_id
            )

            # 5. 处理文档内容（异步或同步）
            document, chunks_count = self.process_document(db, document.id)

            logger.info(f"文件上传和处理完成: ID={document.id}, 块数={chunks_count}")

            return document

        except Exception as e:
            logger.error(f"文件上传和处理失败: {e}")
            raise

    def get_document(self, db: Session, document_id: int) -> Optional[Document]:
        """获取文档"""
        return db.query(Document).filter(Document.id == document_id).first()

    def get_documents(
            self,
            db: Session,
            skip: int = 0,
            limit: int = 10,
            user_id: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        """获取文档列表"""
        query = db.query(Document)

        if user_id:
            query = query.filter(Document.user_id == user_id)

        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

        return documents, total

    def delete_document(self, db: Session, document_id: int) -> bool:
        """删除文档"""
        try:
            document = self.get_document(db, document_id)
            if not document:
                return False

            # 删除物理文件
            if os.path.exists(document.file_path):
                try:
                    os.remove(document.file_path)
                    logger.info(f"删除物理文件: {document.file_path}")
                except Exception as e:
                    logger.error(f"删除物理文件失败: {e}")

            # 删除数据库记录（会级联删除文档块）
            db.delete(document)
            db.commit()

            logger.info(f"删除文档成功: ID={document_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"删除文档失败 (ID={document_id}): {e}")
            return False

    def search_documents(
            self,
            db: Session,
            query_text: str,
            limit: int = 5,
            threshold: float = 0.7
    ) -> List:
        """
        搜索相关文档分块
        
        Args:
            db: 数据库会话
            query_text: 查询文本
            limit: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            List[DocumentSearchResult]: 搜索结果列表
        """
        try:
            from app.schemas.document import DocumentSearchResult
            
            # 使用向量服务进行搜索
            results = vector_service.search_similar(
                db=db,
                query=query_text,
                limit=limit,
                threshold=threshold
            )
            
            return results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []

    def _get_safe_filename(self, filename: str) -> str:
        """获取安全的文件名（避免路径遍历和特殊字符）"""
        import re
        from datetime import datetime

        # 移除路径信息，只保留文件名
        safe_name = os.path.basename(filename)

        # 移除特殊字符
        safe_name = re.sub(r'[^\w\-_.]', '_', safe_name)

        # 添加时间戳避免冲突
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(safe_name)

        return f"{timestamp}_{name}{ext}"


# 创建全局实例
document_service = DocumentService()