"""
所有 Schema 类的统一导出
"""

# 从 base.py
from app.schemas.base import BaseSchema

# 从 chat_message.py - 导出所有可能需要的
from app.schemas.chat_message import (
    SenderType,
    ChatMessageBase,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageInDB,
    ChatMessageResponse,
    format_message_time
)

# 从 chat_history.py - 导出所有可能需要的
from app.schemas.chat_history import (
    ChatHistoryBase,
    ChatHistoryCreate,
    ChatHistoryUpdate,
    ChatHistoryInDB,
    ChatHistoryResponse,
    ChatHistoryListResponse
)

# 从 api.py - 导出所有可能需要的
from app.schemas.api import (
    BaseResponse,
    ErrorResponse,
    SuccessResponse,
    ChatRequest,
    ChatGenerateRequest,
    ChatResponse,
    ChatGenerateResponse,
    PaginationParams
)

# 导出所有
__all__ = [
    # 基础
    "BaseSchema",
    
    # 消息相关
    "SenderType",
    "ChatMessageBase",
    "ChatMessageCreate",
    "ChatMessageUpdate",
    "ChatMessageInDB",
    "ChatMessageResponse",
    "format_message_time",
    
    # 历史相关
    "ChatHistoryBase",
    "ChatHistoryCreate",
    "ChatHistoryUpdate",
    "ChatHistoryInDB",
    "ChatHistoryResponse",
    "ChatHistoryListResponse",
    
    # API相关
    "BaseResponse",
    "ErrorResponse",
    "SuccessResponse",
    "ChatRequest",
    "ChatGenerateRequest",
    "ChatResponse",
    "ChatGenerateResponse",
    "PaginationParams",
]
