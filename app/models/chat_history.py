# app/models/chat_history.py
"""
聊天历史模型 - 修复类型标注版
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ChatHistory(BaseModel):
    """聊天历史模型"""
    __tablename__ = "chat_histories"

    # 🔥 类型标注（仅用于类型检查）
    if TYPE_CHECKING:
        title: str

    # 表字段
    title = Column(String(255), nullable=False, default="新对话", comment="聊天标题")

    # 关系定义
    messages = relationship(
        "ChatMessage",
        back_populates="chat_history",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ChatMessage.created_at"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault('title', "新对话")
        super().__init__(**kwargs)

    def update_title_from_messages(self):
        """根据第一条消息更新标题"""
        if self.messages and hasattr(self.messages, 'count') and self.messages.count() > 0:
            from app.models.chat_message import ChatMessage
            first_message = self.messages.order_by(ChatMessage. created_at).first()
            if first_message and first_message.content:
                content = first_message.content. strip()
                if len(content) > 30:
                    self.title = content[:27] + "..."
                else:
                    self.title = content

    def get_last_message(self):
        """获取最后一条消息"""
        if self.messages and hasattr(self.messages, 'first'):
            from app.models.chat_message import ChatMessage
            return self.messages.order_by(ChatMessage. created_at.desc()).first()
        return None