"""
API路由包初始化文件 - 修改版（按前端要求）
"""

from fastapi import APIRouter

from app.api.routes import chat_histories, ai_chat

# 创建主路由器 - 按前端要求，无前缀
api_router = APIRouter()

# 注册前端要求的路由（按前端规范）
api_router.include_router(chat_histories.router)  # /chathistories 相关
api_router.include_router(ai_chat.router)        # /chat 相关

# 注意：chat_messages 路由前端规范中没有单独提到，暂时不注册
# 这些功能通过 chat_histories 和 ai_chat 接口提供