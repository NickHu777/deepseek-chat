# app/api/routes/__init__.py
"""
API路由模块
"""
from app.api.routes.ai_chat import router as ai_chat_router
from app.api.routes.chat_histories import router as chat_histories_router
from app.api.routes.chat_messages import router as chat_messages_router

# 尝试导入文档路由
try:
    from app.api.routes.documents import router as documents_router
    DOCUMENTS_AVAILABLE = True
except ImportError:
    documents_router = None
    DOCUMENTS_AVAILABLE = False

# 所有路由列表
routers = [
    ai_chat_router,
    chat_histories_router,
    chat_messages_router,
]

if DOCUMENTS_AVAILABLE and documents_router:
    routers.append(documents_router)

# 导出
__all__ = [
    "ai_chat_router",
    "chat_histories_router",
    "chat_messages_router",
]

if DOCUMENTS_AVAILABLE:
    __all__.append("documents_router")
__all__.append("routers")