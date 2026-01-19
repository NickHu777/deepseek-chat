"""
API错误处理 - 完整版
"""

from fastapi import HTTPException, status
from app.services import (
    NotFoundException,
    ValidationException,
    DatabaseException,
    AIException
)

def handle_service_exception(exc):
    """处理服务层异常"""
    
    if isinstance(exc, NotFoundException):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    
    elif isinstance(exc, ValidationException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    
    elif isinstance(exc, DatabaseException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据库操作失败"
        )
    
    elif isinstance(exc, AIException):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI服务暂时不可用"
        )
    
    else:
        # 其他异常
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
