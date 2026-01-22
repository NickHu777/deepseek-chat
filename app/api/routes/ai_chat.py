"""
AI聊天API路由 - 修改版（按前端规范）
实现：POST /chat, POST /chat/generate, 流式接口
完全按前端要求：无前缀，正确格式返回
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

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
    "/chat-histories/{chat_history_id}/messages",
    summary="发送消息并获取AI回复",
    description="在指定的聊天历史中发送消息并获取AI回复"
)
async def send_chat_message(
        chat_history_id: int,
        message: str,  # 直接接收消息字符串
        message_service: ChatMessageService = Depends(get_chat_message_service),
        ai_service: AIService = Depends(get_ai_service),
        db: Session = Depends(get_db_session)
):
    """
    在聊天历史中发送消息并获取AI回复

    - **chat_history_id**: 聊天历史ID（路径参数）
    - **message**: 用户消息内容

    响应格式：
    {
      "success": true,
      "user_message": {...},
      "ai_reply": {...}
    }
    """
    try:
        import asyncio
        from app.services import ChatHistoryService
        from app.schemas import ChatRequest

        # 构建 ChatRequest 对象
        chat_request = ChatRequest(message=message, chatId=chat_history_id)

        # 1. 处理用户消息（保存到数据库）- 在线程池中执行避免阻塞
        user_message = await asyncio.to_thread(
            message_service.create_user_message,
            chat_history_id=chat_request.chatId,
            content=chat_request.message
        )

        # 2. 获取对话上下文
        context = await asyncio.to_thread(
            message_service.get_conversation_context,
            chat_request.chatId
        )

        # 3. 生成AI回复 - AI调用可能耗时，使用线程池
        ai_result = await asyncio.to_thread(
            ai_service.process_chat_with_context,
            user_message.model_dump(),
            context
        )
        ai_reply_content = ai_result["reply"]

        # 4. 保存AI回复到数据库
        ai_message = await asyncio.to_thread(
            message_service.create_ai_message,
            chat_history_id=chat_request.chatId,
            content=ai_reply_content
        )

        # 5. 更新聊天历史标题（如果是第一条消息）
        if len(context) == 0:
            history_service = ChatHistoryService(db)
            await asyncio.to_thread(
                history_service.update_chat_history_title_from_messages,
                chat_request.chatId
            )

        # 6. 按前端格式返回 - 直接使用 ChatMessageResponse 对象的字段
        return {
            "success": True,
            "user_message": {
                "id": user_message.id,
                "content": user_message.content,
                "sender": user_message.sender,
                "time": user_message.time
            },
            "ai_reply": {
                "id": ai_message.id,
                "content": ai_message.content,
                "sender": ai_message.sender,
                "time": ai_message.time
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
    "/completions",
    summary="获取AI回复（独立接口）",
    description="根据用户输入生成AI回复，无上下文"
)
async def generate_ai_reply(
        prompt: str,  # 直接接收 prompt 字符串
        ai_service: AIService = Depends(get_ai_service)
):
    """
    生成AI回复（独立接口）

    - **prompt**: 用户的输入内容

    响应格式：
    {
      "success": true,
      "reply": "AI生成的回复内容"
    }
    """
    try:
        import asyncio
        from app.schemas import ChatGenerateRequest
        
        # 构建 ChatGenerateRequest 对象
        generate_request = ChatGenerateRequest(prompt=prompt)
        
        # AI调用可能耗时，使用线程池避免阻塞
        result = await asyncio.to_thread(
            ai_service.process_chat_generate_request,
            generate_request
        )

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


# ============== 流式对话接口 ==============

@router.post(
    "/chat-histories/{chat_history_id}/messages/stream",
    summary="发送消息并获取AI流式回复（带上下文）",
    description="在指定的聊天历史中发送消息并以流式方式获取AI回复"
)
async def send_chat_message_stream(
        chat_history_id: int,
        message: str,
        message_service: ChatMessageService = Depends(get_chat_message_service),
        ai_service: AIService = Depends(get_ai_service),
        db: Session = Depends(get_db_session)
):
    """
    流式对话接口（带上下文） - AI 逐字输出

    与 /chat-histories/{id}/messages 功能相同，但使用流式输出
    
    返回格式（SSE）：
    data: {"type": "token", "content": "你"}
    data: {"type": "token", "content": "好"}
    data: {"type": "done", "message_id": 123}
    """
    async def event_generator():
        import asyncio
        try:
            from app.services import ChatHistoryService
            from app.schemas import ChatRequest

            # 🔥 立即发送开始事件，让前端知道请求已收到
            yield f"data: {json.dumps({'type': 'start', 'message': 'AI正在思考...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)  # 确保立即发送

            # 1. 保存用户消息 - 使用线程池避免阻塞
            chat_request = ChatRequest(message=message, chatId=chat_history_id)
            user_message = await asyncio.to_thread(
                message_service.create_user_message,
                chat_history_id=chat_request.chatId,
                content=chat_request.message
            )

            # 发送用户消息已保存的确认
            yield f"data: {json.dumps({'type': 'user_message', 'message_id': user_message.id}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)  # 确保立即发送

            # 2. 获取对话上下文 - 使用线程池
            context = await asyncio.to_thread(
                message_service.get_conversation_context,
                chat_request.chatId
            )

            # 3. 流式生成 AI 回复 - 在线程中运行同步生成器
            full_reply = ""
            
            # 🔥 使用 run_in_executor 在线程池中运行同步生成器
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            # 创建同步生成器
            stream_gen = ai_service.generate_reply_stream(
                prompt=user_message.content,
                context=context
            )
            
            # 在线程池中逐个获取 token
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            while True:
                try:
                    # 在线程池中获取下一个token
                    token = await loop.run_in_executor(executor, lambda: next(stream_gen, None))
                    if token is None:
                        break
                    full_reply += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)  # 🔥 关键：确保每个token立即发送
                except StopIteration:
                    break

            # 4. 保存完整的 AI 回复 - 使用线程池
            ai_message = await asyncio.to_thread(
                message_service.create_ai_message,
                chat_history_id=chat_request.chatId,
                content=full_reply
            )

            # 5. 更新标题 - 使用线程池
            if len(context) == 0:
                history_service = ChatHistoryService(db)
                await asyncio.to_thread(
                    history_service.update_chat_history_title_from_messages,
                    chat_request.chatId
                )

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'message_id': ai_message.id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Encoding": "none"
        }
    )


@router.post(
    "/completions/stream",
    summary="获取AI流式回复（独立接口）",
    description="根据用户输入生成AI流式回复，无上下文"
)
async def generate_ai_reply_stream(
        prompt: str,
        ai_service: AIService = Depends(get_ai_service)
):
    """
    流式独立对话接口（无上下文） - AI 逐字输出

    与 /completions 功能相同，但使用流式输出
    不保存到数据库，不关联聊天历史
    
    返回格式（SSE）：
    data: {"type": "token", "content": "你"}
    data: {"type": "token", "content": "好"}
    data: {"type": "done"}
    """
    async def event_generator():
        import asyncio
        try:
            # 🔥 立即发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': 'AI正在思考...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)  # 确保立即发送
            
            # 流式生成 AI 回复（无上下文） - 在线程中运行同步生成器
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            # 创建同步生成器
            stream_gen = ai_service.generate_reply_stream(
                prompt=prompt,
                context=None
            )
            
            # 在线程池中逐个获取 token
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            while True:
                try:
                    token = await loop.run_in_executor(executor, lambda: next(stream_gen, None))
                    if token is None:
                        break
                    yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)  # 🔥 关键：确保每个token立即发送
                except StopIteration:
                    break

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Encoding": "none"
        }
    )
