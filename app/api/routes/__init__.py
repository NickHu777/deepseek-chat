# app/api/routes/__init__.py
"""
API路由子包初始化文件
"""

from app.api.routes.chat_histories import router as chat_histories_router
from app.api.routes.chat_messages import router as chat_messages_router
from app.api.routes.ai_chat import router as ai_chat_router

__all__ = [
    "chat_histories_router",
    "chat_messages_router",
    "ai_chat_router"
]