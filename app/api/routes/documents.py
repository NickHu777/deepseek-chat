# app/api/routes/documents.py
"""
文档API路由 - 完整实现版
"""
import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.dependencies import get_db_session
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentSearchQuery,
    DocumentSearchResult
)
from app.services.document_service import document_service
from app.services.file_processor import file_processor
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["文档管理"])


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传文档",
    description="上传文档文件并自动处理（文本提取、向量化）"
)
async def upload_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(..., description="上传的文件"),
        user_id: Optional[str] = Query(None, description="用户ID"),
        process_immediately: bool = Query(True, description="是否立即处理文档"),
        db: Session = Depends(get_db_session)
):
    """
    上传文档文件
    
    支持的文件格式：
    - PDF (.pdf)
    - Word (.docx, .doc)
    - 文本 (.txt, .md)
    
    流程：
    1. 验证文件类型和大小
    2. 保存文件到服务器
    3. 创建数据库记录
    4. 后台处理：文本提取、分块、向量化
    """
    try:
        # 1. 验证文件类型
        if not file_processor.is_file_allowed(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型。支持的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 2. 验证文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到开头

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件过大，最大支持 {settings.max_file_size_mb} MB"
            )

        logger.info(f"开始上传文档: {file.filename}, 大小: {file_size} bytes, 用户: {user_id}")

        # 3. 保存文件
        saved_path = await document_service.save_uploaded_file(file)
        logger.info(f"文件保存成功: {saved_path}")

        # 4. 创建数据库记录
        document = document_service.create_document_record(
            db=db,
            filename=file.filename,
            file_path=saved_path,
            file_size=file_size,
            user_id=user_id
        )

        # 5. 后台处理文档（如果需要）
        if process_immediately:
            background_tasks.add_task(
                document_service.process_document_background,
                document_id=document.id,
                db_session=db
            )
            logger.info(f"文档已加入后台处理队列: ID={document.id}")

        # 6. 返回响应
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            upload_time=document.upload_time,
            user_id=document.user_id,
            file_metadata=document.file_metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            chunks_count=0,
            chunks=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文档失败: {str(e)}"
        )


@router.get(
    "/documents/test",
    summary="测试文档API",
    description="测试文档API是否正常工作"
)
async def test_documents():
    """测试文档API是否正常工作"""
    return {
        "status": "success",
        "message": "文档API工作正常",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "GET /documents/test",
            "POST /documents",
            "GET /documents",
            "GET /documents/{id}",
            "DELETE /documents/{id}",
            "GET /search/documents",
            "GET /system/status"
        ]
    }


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="获取文档列表",
    description="获取所有已上传的文档列表"
)
async def list_documents(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页大小"),
        user_id: Optional[str] = Query(None, description="用户ID过滤"),
        db: Session = Depends(get_db_session)
):
    """
    获取文档列表
    """
    try:
        # 导入模型
        from app.models.document import Document
        
        # 构建查询
        query = db.query(Document)
        
        # 用户过滤
        if user_id:
            query = query.filter(Document.user_id == user_id)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * size
        documents = query.order_by(Document.created_at.desc()).offset(offset).limit(size).all()
        
        # 转换为响应格式
        items = []
        for doc in documents:
            items.append(DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                file_path=doc.file_path,
                file_type=doc.file_type,
                file_size=doc.file_size,
                upload_time=doc.upload_time,
                user_id=doc.user_id,
                file_metadata=doc.file_metadata or {},
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                chunks_count=len(doc.chunks) if doc.chunks else 0,
                chunks=[]
            ))
        
        return DocumentListResponse(
            items=items,
            total=total,
            page=page,
            size=size
        )

    except Exception as e:
        logger.error(f"获取文档列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="获取文档详情",
    description="根据ID获取单个文档的详细信息"
)
async def get_document(
        document_id: int,
        include_chunks: bool = Query(False, description="是否包含文档分块"),
        db: Session = Depends(get_db_session)
):
    """
    获取文档详情
    """
    try:
        from app.models.document import Document, DocumentChunk
        
        # 查询文档
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档不存在: ID={document_id}"
            )
        
        # 获取分块信息
        chunks = []
        if include_chunks and document.chunks:
            from app.schemas.document import DocumentChunkResponse
            chunks = [
                DocumentChunkResponse(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=chunk.embedding,
                    chunk_metadata=chunk.chunk_metadata or {},
                    created_at=chunk.created_at,
                    updated_at=chunk.updated_at
                )
                for chunk in document.chunks
            ]
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            upload_time=document.upload_time,
            user_id=document.user_id,
            file_metadata=document.file_metadata or {},
            created_at=document.created_at,
            updated_at=document.updated_at,
            chunks_count=len(document.chunks) if document.chunks else 0,
            chunks=chunks
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档详情失败: {str(e)}"
        )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文档",
    description="删除文档及其所有分块和向量"
)
async def delete_document(
        document_id: int,
        db: Session = Depends(get_db_session)
):
    """
    删除文档
    """
    try:
        from app.models.document import Document
        
        # 查询文档
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档不存在: ID={document_id}"
            )
        
        # 删除物理文件
        if os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                logger.info(f"删除文件: {document.file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")
        
        # 删除数据库记录（会级联删除分块）
        db.delete(document)
        db.commit()
        
        logger.info(f"文档删除成功: ID={document_id}")
        
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除文档失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


@router.get(
    "/documents/test",
    summary="测试文档API",
    description="测试文档API是否正常工作"
)
async def test_documents():
    """测试文档API是否正常工作"""
    return {
        "status": "success",
        "message": "文档API工作正常",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "POST /documents - 上传文档",
            "GET /documents - 获取文档列表",
            "GET /documents/{id} - 获取文档详情",
            "DELETE /documents/{id} - 删除文档",
            "GET /search/documents - 搜索文档",
            "GET /system/status - 系统状态"
        ]
    }


@router.get(
    "/search/documents",
    response_model=List[DocumentSearchResult],
    summary="搜索相关文档",
    description="使用向量搜索查找与查询文本相关的文档"
)
async def search_documents(
        q: str = Query(..., description="搜索查询文本"),
        limit: int = Query(5, ge=1, le=100, description="返回结果数量"),
        threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值"),
        db: Session = Depends(get_db_session)
):
    """
    向量搜索文档分块（使用 GET + 查询参数）
    """
    try:
        logger.info(f"文档搜索: query='{q}', limit={limit}, threshold={threshold}")

        # 调用文档服务进行搜索
        results = document_service.search_documents(
            db=db,
            query_text=q,
            limit=limit,
            threshold=threshold
        )
        
        return results

    except Exception as e:
        logger.error(f"文档搜索失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档搜索失败: {str(e)}"
        )


@router.get(
    "/system/status",
    summary="系统状态",
    description="获取文档系统状态和向量服务信息"
)
async def get_system_status():
    """获取系统状态"""
    try:
        from app.config import settings

        # 尝试获取向量服务状态
        vector_status = {"available": False}
        try:
            from app.services.vector_service import vector_service
            vector_status = {
                "available": True,
                "model_loaded": vector_service.is_model_loaded(),
                "dimension": vector_service.dimension
            }
        except Exception as e:
            vector_status["error"] = str(e)

        return {
            "api": {
                "name": "文档向量化系统",
                "version": "1.0.0",
                "status": "active"
            },
            "vector_service": vector_status,
            "configuration": {
                "vector_model": settings.VECTOR_MODEL,
                "upload_dir": settings.UPLOAD_DIR,
                "max_file_size_mb": settings.max_file_size_mb
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态失败: {str(e)}"
        )