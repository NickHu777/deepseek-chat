# app/api/__init__.py
"""
API路由包初始化文件
"""

from fastapi import APIRouter

# 导入现有路由
from app.api.routes import chat_histories, ai_chat

# 创建主路由器
api_router = APIRouter()

# 注册路由
api_router.include_router(chat_histories.router)  # /chathistories
api_router.include_router(ai_chat.router)        # /chat

# 尝试导入文档路由
try:
    from app.api.routes.documents import router as documents_router
    api_router.include_router(documents_router)  # /documents
    print("✅ 文档路由注册成功")
except ImportError as e:
    print(f"⚠️ 文档路由未注册: {e}")