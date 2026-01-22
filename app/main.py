"""
FastAPI 主应用入口 - 修改版（按前端要求）
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中（修复 VS Code 右键运行问题）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.database import engine
from app.models import Base
from app.config import settings
from app.api import api_router
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    在启动时创建表，在关闭时清理资源
    """
    # 启动时
    logger.info("启动 FastAPI 应用...")

    # 创建数据库表（如果不存在）
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建/验证完成")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        # 不阻止应用启动，表可能已存在

    yield  # 应用运行期间

    # 关闭时
    logger.info("关闭 FastAPI 应用...")
    # 可以在这里添加清理代码


# 创建FastAPI应用实例
app = FastAPI(
    title="DeepSeek聊天API",
    description="基于FastAPI的智能聊天后端服务 - 按前端规范实现",
    version="1.1.0",
    docs_url="/docs",  # 始终启用文档
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 配置CORS（跨域资源共享）
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://your-frontend.com"],  # 生产环境指定来源
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


# ============== 全局异常处理 ==============

@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    """处理404错误 - 按前端错误格式"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "请求的资源不存在",
            "code": 404,
            "details": {"path": str(request.url.path)}
        }
    )


@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    """处理500错误 - 按前端错误格式"""
    logger.error(f"服务器内部错误: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "code": 500
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """处理通用异常 - 按前端错误格式"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器发生错误",
            "code": 500
        }
    )


# ============== 健康检查端点 ==============

@app.get("/")
async def root():
    """根端点，显示API信息"""
    return {
        "message": "DeepSeek聊天API服务运行中",
        "version": "2.0.0",
        "docs": "/docs" if settings.DEBUG else None,
        "environment": settings.ENV,
        "debug": settings.DEBUG,
        "api_endpoints": {
            "chat_histories": {
                "GET /chat-histories": "获取所有聊天历史",
                "POST /chat-histories": "创建新聊天历史",
                "GET /chat-histories/{id}": "获取单个聊天历史",
                "PUT /chat-histories/{id}": "更新聊天历史",
                "DELETE /chat-histories/{id}": "删除聊天历史"
            },
            "messages": {
                "POST /chat-histories/{id}/messages": "发送消息并获取AI回复"
            },
            "ai": {
                "POST /completions": "独立生成AI回复（无上下文）"
            },
            "documents": {
                "POST /documents": "上传文档",
                "GET /documents": "获取文档列表",
                "GET /documents/{id}": "获取文档详情",
                "DELETE /documents/{id}": "删除文档"
            },
            "search": {
                "GET /search/documents": "搜索文档"
            },
            "system": {
                "GET /health": "健康检查",
                "GET /system/status": "系统状态"
            }
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    from app.database import test_connection

    db_status = test_connection()

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "environment": settings.ENV,
        "timestamp": datetime.now().isoformat()
    }


# ============== 注册API路由 ==============

# 按前端要求注册路由（无前缀）
app.include_router(api_router)


# ============== 开发环境特定配置 ==============

if __name__ == "__main__":
    """直接运行时的入口（开发环境）"""
    import uvicorn

    logger.info(f"启动开发服务器，环境: {settings.ENV}")
    logger.info(f"数据库: {settings.database_url}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"文档地址: http://localhost:9000/docs")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,  # 开发环境端口
        reload=True,  # 热重载
        log_level="debug" if settings.DEBUG else "info",
        timeout_keep_alive=300,  # 保持连接超时300秒（5分钟）
        timeout_graceful_shutdown=30  # 优雅关闭超时30秒
    )