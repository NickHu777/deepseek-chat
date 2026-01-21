# app/schemas/document.py
"""
文档相关的Pydantic模型
用于数据验证和序列化
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentChunkBase(BaseModel):
    """文档块基础模型"""
    chunk_index: int = Field(..., description="分块索引")
    chunk_text: str = Field(..., description="分块文本")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentChunkCreate(DocumentChunkBase):
    """创建文档块请求模型"""
    pass


class DocumentChunkResponse(DocumentChunkBase):
    """文档块响应模型"""
    id: int
    document_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    """文档基础模型"""
    filename: str = Field(..., description="文件名")
    file_type: Optional[str] = Field(None, description="文件类型")
    file_size: Optional[int] = Field(None, description="文件大小")
    user_id: Optional[str] = Field(None, description="用户ID")
    file_metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentCreate(DocumentBase):
    """创建文档请求模型"""
    file_path: str = Field(..., description="文件路径")


class DocumentUpdate(BaseModel):
    """更新文档请求模型"""
    filename: Optional[str] = None
    file_metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: int
    file_path: str
    upload_time: datetime
    created_at: datetime
    updated_at: datetime
    chunks_count: Optional[int] = 0
    chunks: List[DocumentChunkResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    items: List[DocumentResponse]
    total: int
    page: int
    size: int


# ============ 新增的搜索相关模型 ============

class DocumentSearchQuery(BaseModel):
    """文档搜索查询模型"""
    query: str = Field(..., description="搜索查询文本")
    limit: int = Field(5, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="相似度阈值")


class DocumentSearchResult(BaseModel):
    """文档搜索结果模型"""
    chunk_id: int
    chunk_text: str
    filename: str
    document_id: int
    similarity: float
    metadata: Dict[str, Any]