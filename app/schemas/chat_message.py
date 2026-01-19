# app/schemas/chat_message.py
"""
聊天消息相关的 Pydantic 模式
"""

from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator
from enum import Enum

# 从 base.py 导入基础类，而不是从 __init__.py
from app.schemas.base import BaseSchema


# ============== 枚举类型 ==============

class SenderType(str, Enum):
    """发送者类型枚举"""
    USER = "user"
    AI = "ai"


# ============== 基础模式 ==============

class ChatMessageBase(BaseSchema):
    """聊天消息基础模式"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="消息内容",
        examples=["你好，我需要帮助"]
    )
    sender: SenderType = Field(
        ...,
        description="发送者类型",
        examples=["user"]
    )


# ============== 请求模式 ==============

class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息的请求模式"""
    chat_history_id: int = Field(
        ...,
        gt=0,
        description="关联的聊天历史ID",
        examples=[1]
    )


class ChatMessageUpdate(BaseSchema):
    """更新聊天消息的请求模式"""
    content: Optional[str] = Field(
        None,
        min_length=1,
        max_length=10000,
        description="消息内容"
    )
    sender: Optional[SenderType] = Field(
        None,
        description="发送者类型"
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """内容验证器"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("消息内容不能为空")
        return v


# ============== 响应模式 ==============

class ChatMessageInDB(ChatMessageBase):
    """数据库中的聊天消息模式"""
    id: int = Field(..., description="消息ID", examples=[1])
    chat_history_id: int = Field(..., description="关联的聊天历史ID", examples=[1])
    created_at: datetime = Field(..., description="创建时间")

    @field_validator('sender', mode='before')
    @classmethod
    def validate_sender_before(cls, v):
        """发送者类型预处理验证"""
        if isinstance(v, str):
            v = v.lower()
            if v not in ['user', 'ai']:
                raise ValueError(f"无效的发送者类型: {v}")
        return v


# 在 app/schemas/chat_message.py 中修改 ChatMessageResponse 类

class ChatMessageResponse(ChatMessageInDB):
    """聊天消息响应模式（API返回给前端的格式）"""
    time: str = Field(..., description="前端显示的时间格式", examples=["10:25"])

    @classmethod
    def from_db_model(cls, db_message):
        """从数据库模型创建响应对象"""
        # 检查对象是否具有必要的属性，而不是检查具体类型
        required_attrs = ['id', 'content', 'sender', 'chat_history_id', 'created_at']

        for attr in required_attrs:
            if not hasattr(db_message, attr):
                raise TypeError(f"数据库模型缺少必要属性: {attr}")

        # 获取发送者值（处理枚举类型）
        sender_value = db_message.sender
        if hasattr(sender_value, 'value'):
            sender_value = sender_value.value
        elif isinstance(sender_value, str):
            # 确保是小写
            sender_value = sender_value.lower()

        # 格式化时间：小时:分钟
        time_str = ""
        if hasattr(db_message, 'created_at') and db_message.created_at:
            time_str = db_message.created_at.strftime("%H:%M")

        return cls(
            id=db_message.id,
            content=db_message.content,
            sender=sender_value,
            chat_history_id=db_message.chat_history_id,
            created_at=db_message.created_at,
            time=time_str
        )


# ============== 实用函数 ==============

def format_message_time(created_at: datetime, format_type: str = "short") -> str:
    """
    格式化消息时间
    根据需求文档，前端需要不同的时间格式

    Args:
        created_at: 时间对象
        format_type: 格式类型
            - "short": "10:25"（仅时间）
            - "long": "2026-01-02 14:20"（完整时间）
            - "relative": "今天 10:30" 或 "昨天 15:45"

    Returns:
        格式化后的时间字符串
    """
    if format_type == "short":
        # 例如："10:25"
        return created_at.strftime("%H:%M")
    elif format_type == "long":
        # 例如："2026-01-02 14:20"
        return created_at.strftime("%Y-%m-%d %H:%M")
    elif format_type == "relative":
        # 例如："今天 10:30" 或 "昨天 15:45"
        from datetime import date
        today = date.today()
        message_date = created_at.date()

        if message_date == today:
            return f"今天 {created_at.strftime('%H:%M')}"
        elif message_date == date(today.year, today.month, today.day - 1):
            return f"昨天 {created_at.strftime('%H:%M')}"
        else:
            return created_at.strftime("%Y-%m-%d %H:%M")
    else:
        # 默认返回ISO格式
        return created_at.isoformat()