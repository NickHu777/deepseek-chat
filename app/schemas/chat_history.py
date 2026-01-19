# app/schemas/chat_history.py - 完整版
"""
聊天历史相关的 Pydantic 模式
"""

from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import Field, field_validator

# 从 base.py 导入基础类
from app.schemas.base import BaseSchema
from app.schemas.chat_message import ChatMessageResponse, format_message_time


# ============== 基础模式 ==============

class ChatHistoryBase(BaseSchema):
    """聊天历史基础模式"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="聊天标题",
        examples=["如何学习前端开发"]
    )


# ============== 请求模式 ==============

class ChatHistoryCreate(ChatHistoryBase):
    """创建聊天历史的请求模式"""
    messages: Optional[List[dict]] = Field(
        default_factory=list,
        description="初始消息列表"
    )

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """标题验证器"""
        v = v.strip()
        if not v:
            raise ValueError("聊天标题不能为空")
        return v


class ChatHistoryUpdate(ChatHistoryBase):
    """更新聊天历史的请求模式"""
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="聊天标题"
    )


# ============== 响应模式 ==============

class ChatHistoryInDB(ChatHistoryBase):
    """数据库中的聊天历史模式"""
    id: int = Field(..., description="聊天历史ID", examples=[1])
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ChatHistoryResponse(ChatHistoryInDB):
    """聊天历史响应模式（API返回给前端的格式）"""
    messages: List[ChatMessageResponse] = Field(
        default_factory=list,
        description="消息列表"
    )
    date: str = Field(..., description="前端显示的日期格式", examples=["今天 10:30"])

    @classmethod
    def from_db_model(cls, db_history, include_messages: bool = True):
        """从数据库模型创建响应对象"""
        # 检查对象是否具有必要的属性
        required_attrs = ['id', 'title', 'created_at', 'updated_at']

        for attr in required_attrs:
            if not hasattr(db_history, attr):
                raise TypeError(f"数据库模型缺少必要属性: {attr}")

        # 格式化日期：相对时间（今天/昨天/具体日期）
        today = datetime.now().date()
        history_date = db_history.created_at.date()

        if history_date == today:
            date_str = f"今天 {db_history.created_at.strftime('%H:%M')}"
        elif history_date == today - timedelta(days=1):
            date_str = f"昨天 {db_history.created_at.strftime('%H:%M')}"
        else:
            date_str = db_history.created_at.strftime("%Y-%m-%d %H:%M")

        # 转换消息
        messages = []
        if include_messages and hasattr(db_history, 'messages'):
            # 确保我们有一个可迭代的消息列表
            messages_iter = db_history.messages
            if hasattr(messages_iter, 'all'):
                # SQLAlchemy 的 relationship (lazy='dynamic')
                messages_iter = messages_iter.all()

            # 确保消息按时间排序
            sorted_messages = sorted(
                messages_iter,
                key=lambda msg: msg.created_at if hasattr(msg, 'created_at') else 0
            )

            messages = [
                ChatMessageResponse.from_db_model(msg)
                for msg in sorted_messages
                if hasattr(msg, 'id') and hasattr(msg, 'content')
            ]

        return cls(
            id=db_history.id,
            title=db_history.title,
            created_at=db_history.created_at,
            updated_at=db_history.updated_at,
            messages=messages,
            date=date_str
        )


# ============== 列表响应模式 ==============

class ChatHistoryListResponse(BaseSchema):
    """聊天历史列表响应模式"""
    items: List[ChatHistoryResponse] = Field(
        ...,
        description="聊天历史列表"
    )
    total: int = Field(
        ...,
        ge=0,
        description="总数量",
        examples=[10]
    )

    @classmethod
    def from_db_models(cls, db_histories, total_count: int):
        """从数据库模型列表创建响应对象"""
        items = [
            ChatHistoryResponse.from_db_model(history, include_messages=False)
            for history in db_histories
        ]

        return cls(
            items=items,
            total=total_count
        )