"""
聊天历史API路由 - 修改版（按前端规范）
实现：GET /chathistories, POST /chathistories, PUT /chathistories/{id}
完全按前端要求：无前缀，直接返回数据，无包装
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db_session,
    get_chat_history_service,
    verify_chat_history_exists
)
from app.api.errors import handle_service_exception
from app.schemas import (
    ChatHistoryCreate,
    ChatHistoryUpdate,
    ChatHistoryResponse
)
from app.services import ChatHistoryService
from app.services.exceptions import ServiceException

# 创建路由器 - 注意：不要前缀，路径在装饰器中明确指定
router = APIRouter(tags=["聊天历史管理"])


@router.get(
    "/chathistories",
    response_model=List[ChatHistoryResponse],
    summary="获取所有聊天历史",
    description="获取聊天历史列表，包含所有消息"
)
async def get_all_chat_histories(
        chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    """
    获取所有聊天历史 - 按前端规范

    返回：ChatHistoryResponse 数组，每个包含完整的 messages
    """
    try:
        # 获取所有历史（不分页，前端规范中没有分页）
        result = chat_history_service.get_all_chat_histories()

        # 前端需要每个历史都包含完整消息，所以单独获取每个历史的详情
        histories_with_messages = []
        for history_item in result.items:
            # 获取每个历史的完整消息
            full_history = chat_history_service.get_chat_history(
                history_item.id,
                include_messages=True
            )
            histories_with_messages.append(full_history)

        # 按前端示例返回数据（直接返回数组，没有包装）
        return histories_with_messages

    except ServiceException as e:
        # 转换为前端错误格式
        raise HTTPException(
            status_code=400 if hasattr(e, 'code') else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"获取聊天历史列表失败: {str(e)}",
                "code": 500
            }
        )


@router.post(
    "/chathistories",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新的聊天历史",
    description="创建一个新的聊天历史记录"
)
async def create_chat_history(
        chat_history_data: ChatHistoryCreate,
        chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    """
    创建新的聊天历史 - 按前端规范

    - **title**: 聊天标题
    - **messages**: 初始消息列表（可以为空数组）

    注意：前端示例中创建后会自动添加一条AI欢迎消息
    """
    try:
        # 创建聊天历史（服务层会处理AI欢迎消息）
        # 注意：需要修改服务层以支持自动添加AI欢迎消息
        result = chat_history_service.create_chat_history_with_welcome(
            chat_history_data.title
        )

        # 直接返回创建的历史（包含AI欢迎消息）
        return result

    except ServiceException as e:
        raise HTTPException(
            status_code=400 if hasattr(e, 'code') else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"创建聊天历史失败: {str(e)}",
                "code": 500
            }
        )


@router.get(
    "/chathistories/{chat_history_id}",
    response_model=ChatHistoryResponse,
    summary="获取单个聊天历史",
    description="获取指定ID的聊天历史详情，包含所有消息"
)
async def get_chat_history(
        chat_history_id: int,
        chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    """
    获取单个聊天历史详情 - 按前端规范

    - **chat_history_id**: 聊天历史ID（路径参数）
    """
    try:
        # 获取包含所有消息的聊天历史
        result = chat_history_service.get_chat_history(
            chat_history_id,
            include_messages=True
        )

        return result

    except ServiceException as e:
        raise HTTPException(
            status_code=404 if "未找到" in e.message else 400,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"获取聊天历史详情失败: {str(e)}",
                "code": 500
            }
        )


@router.put(
    "/chathistories/{chat_history_id}",
    response_model=ChatHistoryResponse,
    summary="更新聊天历史",
    description="更新指定ID的聊天历史信息"
)
async def update_chat_history(
        chat_history_id: int,
        update_data: ChatHistoryUpdate,
        chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    """
    更新聊天历史 - 按前端规范

    - **chat_history_id**: 聊天历史ID（路径参数）
    - **title**: 新的聊天标题（请求体）
    """
    try:
        result = chat_history_service.update_chat_history(
            chat_history_id,
            update_data
        )

        return result

    except ServiceException as e:
        raise HTTPException(
            status_code=400 if hasattr(e, 'code') else 500,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"更新聊天历史失败: {str(e)}",
                "code": 500
            }
        )


@router.delete(
    "/chathistories/{chat_history_id}",
    summary="删除聊天历史",
    description="删除指定ID的聊天历史及其所有消息"
)
async def delete_chat_history(
        chat_history_id: int,
        chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
):
    """
    删除聊天历史 - 按前端错误格式返回

    - **chat_history_id**: 聊天历史ID（路径参数）
    """
    try:
        result = chat_history_service.delete_chat_history(chat_history_id)

        # 前端删除成功返回什么？规范中没有明确，我们返回简单成功消息
        return {
            "success": True,
            "message": "聊天历史删除成功",
            "deleted_id": chat_history_id
        }

    except ServiceException as e:
        raise HTTPException(
            status_code=404 if "未找到" in e.message else 400,
            detail={
                "success": False,
                "error": e.message,
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"删除聊天历史失败: {str(e)}",
                "code": 500
            }
        )

# ============== 额外端点（可选，按前端规范没有这些） ==============

# 以下端点前端规范中没有明确要求，暂时注释掉
# 如果需要，可以取消注释

# @router.get(
#     "/chathistories/{chat_history_id}/messages",
#     response_model=List[ChatMessageResponse],
#     summary="获取聊天历史的所有消息",
#     description="获取指定聊天历史的所有消息列表"
# )
# async def get_chat_history_messages(
#     chat_history_id: int,
#     chat_history_service: ChatHistoryService = Depends(get_chat_history_service)
# ):
#     """
#     获取聊天历史的所有消息 - 按前端规范可能不需要
#     """
#     try:
#         # 直接通过历史服务获取消息
#         history = chat_history_service.get_chat_history(
#             chat_history_id,
#             include_messages=True
#         )

#         return history.messages

#     except ServiceException as e:
#         raise HTTPException(
#             status_code=404 if "未找到" in e.message else 400,
#             detail={
#                 "success": False,
#                 "error": e.message,
#                 "code": e.code if hasattr(e, 'code') else 500
#             }
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={
#                 "success": False,
#                 "error": f"获取消息列表失败: {str(e)}",
#                 "code": 500
#             }
#         )