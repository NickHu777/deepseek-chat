"""
聊天历史服务 - 完整修复版
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.chat_history import ChatHistory
from app.models.chat_message import ChatMessage, SenderType
from app.schemas.chat_history import (
    ChatHistoryCreate,
    ChatHistoryUpdate,
    ChatHistoryResponse,
    ChatHistoryListResponse
)
from app.schemas.chat_message import ChatMessageCreate
from app.schemas.api import PaginationParams


class ServiceException(Exception):
    """服务层基础异常"""
    pass


class NotFoundException(ServiceException):
    """资源未找到异常"""
    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} ID {resource_id} 未找到"
        super().__init__(message)


class DatabaseException(ServiceException):
    """数据库操作异常"""
    pass


class ChatHistoryService:
    """聊天历史服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ============== 基础CRUD操作 ==============

    def create_chat_history(self, chat_history_data: ChatHistoryCreate) -> ChatHistoryResponse:
        """
        创建聊天历史
        """
        try:
            # 创建聊天历史
            db_chat_history = ChatHistory(
                title=chat_history_data.title
            )

            self.db.add(db_chat_history)
            self.db.commit()
            self.db.refresh(db_chat_history)

            return ChatHistoryResponse.from_db_model(db_chat_history, include_messages=False)

        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"创建聊天历史失败: {str(e)}")

    def get_chat_history(self, chat_history_id: int, include_messages: bool = True) -> ChatHistoryResponse:
        """
        获取单个聊天历史
        """
        try:
            # 查询聊天历史
            db_chat_history = self.db.query(ChatHistory).filter(
                ChatHistory.id == chat_history_id
            ).first()

            if not db_chat_history:
                raise NotFoundException("聊天历史", chat_history_id)

            return ChatHistoryResponse.from_db_model(db_chat_history, include_messages=include_messages)

        except NotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(f"获取聊天历史失败: {str(e)}")

    def get_all_chat_histories(self, pagination: Optional[PaginationParams] = None) -> ChatHistoryListResponse:
        """
        获取所有聊天历史（分页）
        """
        try:
            # 设置默认分页参数
            if pagination is None:
                pagination = PaginationParams()

            # 查询总数
            total = self.db.query(func.count(ChatHistory.id)).scalar()

            # 查询数据（按创建时间倒序）
            db_chat_histories = self.db.query(ChatHistory).order_by(
                desc(ChatHistory.created_at)
            ).offset(pagination.offset).limit(pagination.limit).all()

            return ChatHistoryListResponse.from_db_models(db_chat_histories, total)

        except Exception as e:
            raise DatabaseException(f"获取聊天历史列表失败: {str(e)}")

    def update_chat_history(self, chat_history_id: int, update_data: ChatHistoryUpdate) -> ChatHistoryResponse:
        """
        更新聊天历史
        """
        try:
            # 查询聊天历史
            db_chat_history = self.db.query(ChatHistory).filter(
                ChatHistory.id == chat_history_id
            ).first()

            if not db_chat_history:
                raise NotFoundException("聊天历史", chat_history_id)

            # 更新字段
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(db_chat_history, field, value)

            db_chat_history.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(db_chat_history)

            return ChatHistoryResponse.from_db_model(db_chat_history, include_messages=False)

        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"更新聊天历史失败: {str(e)}")

    def delete_chat_history(self, chat_history_id: int) -> bool:
        """
        删除聊天历史
        """
        try:
            # 查询聊天历史
            db_chat_history = self.db.query(ChatHistory).filter(
                ChatHistory.id == chat_history_id
            ).first()

            if not db_chat_history:
                raise NotFoundException("聊天历史", chat_history_id)

            # 删除（由于设置了级联删除，关联的消息会自动删除）
            self.db.delete(db_chat_history)
            self.db.commit()

            return True

        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"删除聊天历史失败: {str(e)}")

    # ============== 业务方法 ==============

    def create_chat_history_with_welcome(self, title: str):
        """
        创建聊天历史并自动添加AI欢迎消息 - 按前端示例
        """
        try:
            # 1. 创建聊天历史
            db_chat_history = ChatHistory(title=title)
            self.db.add(db_chat_history)
            self.db.commit()
            self.db.refresh(db_chat_history)

            # 2. 添加AI欢迎消息（按前端示例）
            welcome_message = ChatMessage(
                chat_history_id=db_chat_history.id,
                content="你好！我是AI助手，有什么可以帮助你的吗？",
                sender=SenderType.AI
            )
            self.db.add(welcome_message)
            self.db.commit()

            # 3. 返回包含消息的历史
            return self.get_chat_history(db_chat_history.id, include_messages=True)

        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"创建聊天历史失败: {str(e)}")

    def update_chat_history_title_from_messages(self, chat_history_id: int) -> ChatHistoryResponse:
        """
        根据第一条消息更新聊天历史标题
        """
        try:
            # 查询聊天历史
            db_chat_history = self.db.query(ChatHistory).filter(
                ChatHistory.id == chat_history_id
            ).first()

            if not db_chat_history:
                raise NotFoundException("聊天历史", chat_history_id)

            db_chat_history.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(db_chat_history)

            return ChatHistoryResponse.from_db_model(db_chat_history, include_messages=False)

        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"更新聊天历史标题失败: {str(e)}")
