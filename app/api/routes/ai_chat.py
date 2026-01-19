"""
AI聊天API路由 - 修改版（按前端规范）
实现：POST /chat, POST /chat/generate
完全按前端要求：无前缀，正确格式返回
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db_session,
    get_chat_message_service,
    get_ai_service
)
from app.models import ChatHistory
from app.schemas import (
    ChatRequest,
    ChatGenerateRequest, ChatHistoryResponse
)
from app.services import ChatMessageService, AIService
from app.services.exceptions import ServiceException, DatabaseException

router = APIRouter(tags=["AI聊天"])


@router.post(
    "/chat",
    summary="发送消息并获取AI回复",
    description="发送用户消息到后端AI服务，并接收AI回复"
)
async def send_chat_message(
        chat_request: ChatRequest,
        message_service: ChatMessageService = Depends(get_chat_message_service),
        ai_service: AIService = Depends(get_ai_service),
        db: Session = Depends(get_db_session)
):
    """
    发送消息并获取AI回复 - 按前端规范

    - **message**: 用户发送的消息内容
    - **chatId**: 对话的ID（注意：前端是chatId，我们是chat_id）

    响应格式完全按前端示例：
    {
      "success": true,
      "user_message": {...},
      "ai_reply": {...}
    }
    """
    try:
        from app.services import ChatHistoryService

        # 1. 处理用户消息（保存到数据库）
        request_result = message_service.process_chat_request(chat_request)
        user_message = request_result["user_message"]

        # 2. 获取对话上下文（用于AI生成）
        context = message_service.get_conversation_context(chat_request.chatId)

        # 3. 生成AI回复
        ai_result = ai_service.process_chat_with_context(user_message, context)
        ai_reply_content = ai_result["reply"]

        # 4. 保存AI回复到数据库
        ai_message = message_service.create_ai_message(
            chat_history_id=chat_request.chatId,
            content=ai_reply_content
        )

        # 5. 更新聊天历史标题（如果是第一条消息）
        if len(context) == 0:  # 只有用户消息，没有之前的对话
            history_service = ChatHistoryService(db)
            history_service.update_chat_history_title_from_messages(chat_request.chatId)

        # 6. 按前端格式返回
        return {
            "success": True,
            "user_message": {
                "id": user_message["id"],
                "content": user_message["content"],
                "sender": "user",
                "time": user_message["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(user_message["created_at"], 'strftime')
                else user_message["created_at"]
            },
            "ai_reply": {
                "id": ai_message.id,
                "content": ai_message.content,
                "sender": "ai",
                "time": ai_message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if ai_message.created_at else ""
            }
        }

    except ServiceException as e:
        raise HTTPException(
            status_code=400 if hasattr(e, 'code') else 500,
            detail={
                "success": False,
                "error":  str(e),
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"处理聊天消息失败: {str(e)}",
                "code": 500
            }
        )


@router.post(
    "/chat/generate",
    summary="获取AI回复（独立接口）",
    description="根据用户输入生成AI回复"
)
async def generate_ai_reply(
        generate_request: ChatGenerateRequest,
        ai_service: AIService = Depends(get_ai_service)
):
    """
    生成AI回复（独立接口） - 按前端规范

    - **prompt**: 用户的输入内容

    响应格式完全按前端示例：
    {
      "success": true,
      "reply": "AI生成的回复内容"
    }
    """
    try:
        result = ai_service.process_chat_generate_request(generate_request)

        # 按前端格式返回
        return {
            "success": True,
            "reply": result["reply"]
        }

    except ServiceException as e:
        raise HTTPException(
            status_code=400 if hasattr(e, 'code') else 500,
            detail={
                "success": False,
                "error": str(e),
                "code": e.code if hasattr(e, 'code') else 500
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": f"生成AI回复失败: {str(e)}",
                "code": 500
            }
        )


# ============== 需要修改服务层的部分 ==============

# 注意：需要在 app/services/chat_history_service.py 中添加以下方法：

def create_chat_history_with_welcome(self, title: str) -> ChatHistoryResponse:
    """
    创建聊天历史并自动添加AI欢迎消息 - 按前端示例

    前端示例中，创建新对话后会返回一条AI欢迎消息
    """
    try:
        # 1. 创建聊天历史
        db_chat_history = ChatHistory(title=title)
        self.db.add(db_chat_history)
        self.db.commit()
        self.db.refresh(db_chat_history)

        # 2. 添加AI欢迎消息（按前端示例）
        from app.models import ChatMessage, SenderType
        welcome_message = ChatMessage(
            chat_history_id=db_chat_history.id,
            content="你好！我是AI助手，有什么可以帮助你的吗？",
            sender=SenderType.AI
        )
        self.db.add(welcome_message)
        self.db.commit()
        self.db.refresh(welcome_message)

        # 3. 返回包含消息的历史
        return ChatHistoryResponse.from_db_model(
            db_chat_history,
            include_messages=True
        )

    except Exception as e:
        self.db.rollback()
        raise DatabaseException(f"创建聊天历史失败: {str(e)}")