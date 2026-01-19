# app/api/routes/chat_messages.py
"""
聊天消息API路由
实现：消息相关的API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_chat_message_service
from app.api.errors import handle_service_exception
from app.schemas import (
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageResponse,
    SuccessResponse
)
from app.services import ChatMessageService
from app.services.exceptions import ServiceException

router = APIRouter(prefix="/messages", tags=["聊天消息管理"])


@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建聊天消息",
    description="创建一条新的聊天消息"
)
async def create_chat_message(
        message_data: ChatMessageCreate,
        message_service: ChatMessageService = Depends(get_chat_message_service)
):
    """
    创建聊天消息

    - **content**: 消息内容
    - **sender**: 发送者类型（user/ai）
    - **chat_history_id**: 关联的聊天历史ID
    """
    try:
        result = message_service.create_chat_message(message_data)

        return SuccessResponse(
            data=result.model_dump(),
            message="消息创建成功",
            code=201
        )

    except ServiceException as e:
        raise handle_service_exception(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建消息失败: {str(e)}"
        )


@router.get(
    "/{message_id}",
    response_model=SuccessResponse,
    summary="获取单个消息",
    description="获取指定ID的聊天消息详情"
)
async def get_chat_message(
        message_id: int,
        message_service: ChatMessageService = Depends(get_chat_message_service)
):
    """
    获取单个消息详情

    - **message_id**: 消息ID（路径参数）
    """
    try:
        result = message_service.get_chat_message(message_id)

        return SuccessResponse(
            data=result.model_dump(),
            message="获取消息详情成功"
        )

    except ServiceException as e:
        raise handle_service_exception(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息详情失败: {str(e)}"
        )


@router.put(
    "/{message_id}",
    response_model=SuccessResponse,
    summary="更新聊天消息",
    description="更新指定ID的聊天消息"
)
async def update_chat_message(
        message_id: int,
        update_data: ChatMessageUpdate,
        message_service: ChatMessageService = Depends(get_chat_message_service)
):
    """
    更新聊天消息

    - **message_id**: 消息ID（路径参数）
    - **content**: 新的消息内容（可选）
    - **sender**: 新的发送者类型（可选）
    """
    try:
        result = message_service.update_chat_message(message_id, update_data)

        return SuccessResponse(
            data=result.model_dump(),
            message="消息更新成功"
        )

    except ServiceException as e:
        raise handle_service_exception(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新消息失败: {str(e)}"
        )


@router.delete(
    "/{message_id}",
    response_model=SuccessResponse,
    summary="删除聊天消息",
    description="删除指定ID的聊天消息"
)
async def delete_chat_message(
        message_id: int,
        message_service: ChatMessageService = Depends(get_chat_message_service)
):
    """
    删除聊天消息

    - **message_id**: 消息ID（路径参数）
    """
    try:
        result = message_service.delete_chat_message(message_id)

        return SuccessResponse(
            data={"deleted": result},
            message="消息删除成功"
        )

    except ServiceException as e:
        raise handle_service_exception(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除消息失败: {str(e)}"
        )