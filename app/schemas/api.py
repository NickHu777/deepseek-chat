"""
API 相关的请求/响应模式 - 完整修复版
"""

from typing import Optional, Any, Dict
from pydantic import Field, field_validator
from app.schemas. base import BaseSchema


# ============== 基础响应 ==============

class BaseResponse(BaseSchema):
    """基础响应模式"""
    success: bool = Field(... , description="请求是否成功", examples=[True])
    message: Optional[str] = Field(None, description="响应消息", examples=["操作成功"])


class ErrorResponse(BaseResponse):
    """错误响应模式"""
    error: str = Field(... , description="错误信息", examples=["参数验证失败"])
    code: int = Field(..., ge=400, description="错误代码", examples=[400])
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

    def __init__(self, error: str, code: int = 400, **kwargs):
        super().__init__(success=False, error=error, code=code, **kwargs)


class SuccessResponse(BaseResponse):
    """成功响应模式"""
    data: Optional[Any] = Field(None, description="响应数据")

    def __init__(self, data: Any = None, message: str = "成功", **kwargs):
        super().__init__(success=True, message=message, data=data, **kwargs)


# ============== API 请求模式 ==============

class ChatRequest(BaseSchema):
    """发送消息请求模式"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="用户消息内容",
        examples=["你好，可以帮我学习Python吗？"]
    )
    chatId: int = Field(
        ...,
        gt=0,
        description="聊天历史ID",
        examples=[1],
        alias="chat_id"
    )
    
    @field_validator('chatId')
    @classmethod
    def validate_chat_id(cls, v):
        """验证chatId"""
        if v <= 0:
            raise ValueError("chatId必须大于0")
        return v


class ChatGenerateRequest(BaseSchema):
    """生成AI回复请求模式"""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="用户输入内容",
        examples=["解释一下什么是RESTful API"]
    )


# ============== API 响应模式 ==============

class ChatResponse(BaseSchema):
    """聊天响应模式"""
    success: bool = Field(..., description="是否成功", examples=[True])
    user_message: Dict[str, Any] = Field(... , description="用户消息")
    ai_reply: Dict[str, Any] = Field(... , description="AI回复")


class ChatGenerateResponse(BaseSchema):
    """AI生成响应模式"""
    success:  bool = Field(..., description="是否成功", examples=[True])
    reply: str = Field(..., description="AI回复内容", examples=["RESTful API是一种设计风格... "])


# ============== 分页参数 ==============

class PaginationParams(BaseSchema):
    """分页参数模式（修复版）"""
    # 🔥 使用 default 参数（Pydantic v2 正确语法）
    page:  int = Field(default=1, ge=1, description="页码", examples=[1])
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量", examples=[10])

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """计算限制数量"""
        return self.page_size