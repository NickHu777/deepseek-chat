# app/models/document.py
"""
文档和文档块模型
用于向量化存储和管理
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, BigInteger, JSON, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Document(BaseModel):
    """文档模型"""
    __tablename__ = "documents"

    # 覆盖父类的 id 定义，使用更明确的配置
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text)
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    upload_time = Column(DateTime, default=datetime.now, nullable=False)
    user_id = Column(String(100))
    file_metadata = Column(JSON, default={}, name="metadata")  # 改名为file_metadata，数据库列名为metadata

    # 关系
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"


class DocumentChunk(BaseModel):
    """文档分块模型"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON)  # 存储向量（列表形式），pgvector会处理
    chunk_metadata = Column(JSON, default={}, name="metadata")  # 改名为chunk_metadata，数据库列名为metadata

    # 关系
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"