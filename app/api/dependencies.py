"""
依赖项定义 - 清理版
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy. orm import Session

from app.database import get_db

def get_db_session() -> Session:
    """获取数据库会话"""
    db_generator = get_db()
    try:
        return next(db_generator)
    except StopIteration:
        from app.database import SessionLocal
        return SessionLocal()

def get_chat_history_service(db: Session = Depends(get_db_session)):
    """获取聊天历史服务"""
    from app.services.chat_history_service import ChatHistoryService
    return ChatHistoryService(db)

def get_chat_message_service(db: Session = Depends(get_db_session)):
    """获取聊天消息服务"""
    from app.services.chat_message_service import ChatMessageService
    return ChatMessageService(db)

def get_ai_service():
    """��取AI服务"""
    from app.services. ai_service import AIService
    return AIService()

def verify_chat_history_exists(
    chat_history_id: int,
    chat_history_service = Depends(get_chat_history_service)
):
    """验证聊天历史是否存在"""
    try:
        return chat_history_service.get_chat_history(chat_history_id, include_messages=False)
    except Exception as e:
        if "未找到" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"聊天历史 ID {chat_history_id} 不存在"
            )
        raise