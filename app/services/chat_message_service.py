# app/services/chat_message_service.py
"""
聊天消息服务
作用：处理聊天消息的业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.models import ChatMessage, ChatHistory, SenderType
from app.schemas import (
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageResponse,
    ChatRequest
)
from app.services.exceptions import (
    NotFoundException,
    ValidationException,
    DatabaseException
)


class ChatMessageService:
    """聊天消息服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ============== 基础CRUD操作 ==============

    def create_chat_message(self, message_data: ChatMessageCreate) -> ChatMessageResponse:
        """
        创建聊天消息

        Args:
            message_data: 消息创建数据

        Returns:
            创建的消息响应
        """
        try:
            # 验证聊天历史是否存在
            chat_history = self.db.query(ChatHistory).filter(
                ChatHistory.id == message_data.chat_history_id
            ).first()

            if not chat_history:
                raise NotFoundException("聊天历史", message_data.chat_history_id)

            # 创建消息
            db_message = ChatMessage(
                content=message_data.content,
                sender=message_data.sender,
                chat_history_id=message_data.chat_history_id
            )

            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)

            return ChatMessageResponse.from_db_model(db_message)

        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"创建聊天消息失败: {str(e)}")

    def get_chat_message(self, message_id: int) -> ChatMessageResponse:
        """
        获取单个聊天消息

        Args:
            message_id: 消息ID

        Returns:
            消息响应
        """
        try:
            db_message = self.db.query(ChatMessage).filter(
                ChatMessage.id == message_id
            ).first()

            if not db_message:
                raise NotFoundException("聊天消息", message_id)

            return ChatMessageResponse.from_db_model(db_message)

        except NotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(f"获取聊天消息失败: {str(e)}")

    def get_messages_by_chat_history(
            self,
            chat_history_id: int,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[ChatMessageResponse]:
        """
        获取指定聊天历史的所有消息

        Args:
            chat_history_id: 聊天历史ID
            limit: 限制数量
            offset: 偏移量

        Returns:
            消息响应列表
        """
        try:
            # 验证聊天历史是否存在
            chat_history = self.db.query(ChatHistory).filter(
                ChatHistory.id == chat_history_id
            ).first()

            if not chat_history:
                raise NotFoundException("聊天历史", chat_history_id)

            # 构建查询
            query = self.db.query(ChatMessage).filter(
                ChatMessage.chat_history_id == chat_history_id
            ).order_by(asc(ChatMessage.created_at))

            # 应用分页
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            db_messages = query.all()

            return [ChatMessageResponse.from_db_model(msg) for msg in db_messages]

        except NotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(f"获取聊天消息列表失败: {str(e)}")

    def update_chat_message(self, message_id: int, update_data: ChatMessageUpdate) -> ChatMessageResponse:
        """
        更新聊天消息

        Args:
            message_id: 消息ID
            update_data: 更新数据

        Returns:
            更新后的消息响应
        """
        try:
            db_message = self.db.query(ChatMessage).filter(
                ChatMessage.id == message_id
            ).first()

            if not db_message:
                raise NotFoundException("聊天消息", message_id)

            # 更新字段
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(db_message, field, value)

            db_message.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(db_message)

            return ChatMessageResponse.from_db_model(db_message)

        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"更新聊天消息失败: {str(e)}")

    def delete_chat_message(self, message_id: int) -> bool:
        """
        删除聊天消息

        Args:
            message_id: 消息ID

        Returns:
            是否删除成功
        """
        try:
            db_message = self.db.query(ChatMessage).filter(
                ChatMessage.id == message_id
            ).first()

            if not db_message:
                raise NotFoundException("聊天消息", message_id)

            self.db.delete(db_message)
            self.db.commit()

            return True

        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(f"删除聊天消息失败: {str(e)}")

    # ============== 业务方法 ==============

    def create_user_message(self, chat_history_id: int, content: str) -> ChatMessageResponse:
        """
        创建用户消息（快捷方法）

        Args:
            chat_history_id: 聊天历史ID
            content: 消息内容

        Returns:
            创建的消息响应
        """
        message_data = ChatMessageCreate(
            content=content,
            sender=SenderType.USER,
            chat_history_id=chat_history_id
        )

        return self.create_chat_message(message_data)

    def create_ai_message(self, chat_history_id: int, content: str) -> ChatMessageResponse:
        """
        创建AI消息（快捷方法）

        Args:
            chat_history_id: 聊天历史ID
            content: 消息内容

        Returns:
            创建的消息响应
        """
        message_data = ChatMessageCreate(
            content=content,
            sender=SenderType.AI,
            chat_history_id=chat_history_id
        )

        return self.create_chat_message(message_data)

    def get_conversation_context(
            self,
            chat_history_id: int,
            max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取对话上下文（用于AI生成）

        Args:
            chat_history_id: 聊天历史ID
            max_messages: 最大消息数量

        Returns:
            上下文消息列表
        """
        try:
            # 获取最新的消息
            messages = self.get_messages_by_chat_history(
                chat_history_id=chat_history_id,
                limit=max_messages
            )

            # 转换为对话上下文格式
            context = []
            for msg in messages:
                context.append({
                    "role": "user" if msg.sender == SenderType.USER else "assistant",
                    "content": msg.content,
                    "time": msg.created_at.isoformat() if msg.created_at else ""
                })

            return context

        except Exception as e:
            raise DatabaseException(f"获取对话上下文失败: {str(e)}")

    def process_chat_request(self, chat_request: ChatRequest) -> Dict[str, Any]:
        """
        处理聊天请求（保存用户消息）

        Args:
            chat_request: 聊天请求数据

        Returns:
            包含用户消息的字典
        """
        try:
            # 创建用户消息
            user_message = self.create_user_message(
                chat_history_id=chat_request.chatId,
                content=chat_request.message
            )

            return {
                "user_message": user_message.model_dump(),
                "chat_history_id": chat_request.chatId
            }

        except Exception as e:
            raise DatabaseException(f"处理聊天请求失败: {str(e)}")