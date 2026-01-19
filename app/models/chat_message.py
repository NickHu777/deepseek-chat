# app/models/chat_message.py
"""
聊天消息模型 - 修复类型标注版
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, Text, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, validates
import enum
from app.models.base import BaseModel


class SenderType(enum.Enum):
    """发送者类型枚举"""
    USER = "user"
    AI = "ai"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    __tablename__ = "chat_messages"

    # 🔥 类型标注（仅用于类型检查）
    if TYPE_CHECKING: 
        content: str
        sender:  SenderType
        chat_history_id: int

    # 表字段
    content = Column(Text, nullable=False, comment="消息内容")
    sender = Column(Enum(SenderType), nullable=False, comment="发送者类型")

    # 外键关系
    chat_history_id = Column(
        Integer,
        ForeignKey("chat_histories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联的聊天历史ID"
    )

    # 关系定义
    chat_history = relationship(
        "ChatHistory",
        back_populates="messages",
        lazy="joined"
    )

    def __init__(self, content=None, sender=None, chat_history_id=None, **kwargs):
        super().__init__(**kwargs)
        if content is not None:
            self.content = content
        if sender is not None:
            if isinstance(sender, str):
                sender = SenderType(sender. lower())
            self.sender = sender
        if chat_history_id is not None:
            self.chat_history_id = chat_history_id

    @validates('sender')
    def validate_sender(self, key, sender):
        """验证发送者类型"""
        if isinstance(sender, str):
            sender = sender.lower()
            if sender not in ['user', 'ai']:
                raise ValueError(f"无效的发送者类型:  {sender}")
            return SenderType(sender)
        elif isinstance(sender, SenderType):
            return sender
        else:
            raise ValueError(f"无效的发送者类型: {type(sender)}")

    @validates('content')
    def validate_content(self, key, content):
        """验证消息内容"""
        if not content or not content.strip():
            raise ValueError("消息内容不能为空")
        if len(content. strip()) > 10000:
            raise ValueError("消息内容过长，最多10000个字符")
        return content. strip()

    def is_user_message(self):
        """判断是否是用户消息"""
        return self.sender == SenderType. USER

    def is_ai_message(self):
        """判断是否是AI消息"""
        return self.sender == SenderType.AI