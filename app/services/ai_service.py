# app/services/ai_service.py
"""
AI服务 - DeepSeek API集成版（完整功能 + 代理修复）
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from openai import OpenAI

from app.schemas import ChatGenerateRequest
from app.services.exceptions import AIException, ValidationException
from app.config import settings


class AIService:
    """AI服务类 - 真实DeepSeek API集成（生产级别）"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化AI服务

        Args:
            api_key:  DeepSeek API密钥
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY

        if not self.api_key:
            raise AIException("DeepSeek API密钥未配置，请在. env中设置DEEPSEEK_API_KEY")

        try:
            # 🔥 关键修复：创建自定义 HTTP 客户端，保留所有生产级功能
            # 注意：httpx 0.27.0 不再支持 proxies 参数，改用 proxy（单数）
            http_client = httpx.Client(
                # 超时配置 - 保证生产环境稳定性
                timeout=httpx.Timeout(
                    connect=10.0,  # 连接超时 10 秒
                    read=60.0,  # 读取超时 60 秒
                    write=10.0,  # 写入超时 10 秒
                    pool=5.0  # 连接池超时 5 秒
            ),
            # 连接池配置 - 提高并发性能
            limits = httpx.Limits(
                max_connections=100,  # 最大连接数
                max_keepalive_connections=20,  # 最大保活连接数
                keepalive_expiry=30.0  # 保活过期时间
            ),
                # 其他配置
            follow_redirects = True,  # 自动跟随重定向
            trust_env = False,  # 🔥 关键：不信任环境变量（禁用代理）
            # 注意：不使用 proxy/proxies 参数，避免版本兼容问题
            )

            # 初始化 OpenAI 客户端（DeepSeek 兼容 OpenAI 接口）
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com",
                http_client=http_client,  # 使用自定义 HTTP 客户端
                max_retries=2,  # API 调用失败时重试次数
                timeout=60.0,  # 总超时时间
                default_headers={  # 自定义请求头
                    "User-Agent": "DeepSeek-Chat-Backend/1.0"
                }
            )

            print(f"✅ AI服务初始化成功")
            print(f"   - 模型: deepseek-chat")
            print(f"   - 连接池: 100 连接, 20 保活")
            print(f"   - 超时:  连接 10s, 读取 60s")
            print(f"   - 重试:  最多 2 次")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ AI服务初始化失败: {error_msg}")
            raise AIException(f"初始化AI客户端失败: {error_msg}")

        # 模型配置
        self.model = "deepseek-chat"
        self.max_tokens = 2000  # 单次回复最大长度
        self.temperature = 1.0  # 创造性（0-2，越高越随机）
        self.top_p = 1.0  # 核采样参数
        self.frequency_penalty = 0.0  # 频率惩罚
        self.presence_penalty = 0.0  # 存在惩罚

    def generate_reply(
            self,
            prompt: str,
            context: Optional[List[Dict[str, Any]]] = None,
            **kwargs  # 支持动态参数覆盖
    ) -> str:
        """
        生成AI回复（支持上下文和参数自定义）

        Args:
            prompt: 用户输入
            context: 对话上下文
            **kwargs: 额外参数（如 temperature, max_tokens）

        Returns:
            AI回复内容
        """
        try:
            # 验证输入
            if not prompt or not prompt.strip():
                raise ValidationException("输入内容不能为空")

            # 构建消息列表
            messages = []

            # 添加系统提示（可以通过 kwargs 自定义）
            system_prompt = kwargs.get(
                'system_prompt',
                "你是一个友好、专业的AI助手。请用简洁、清晰的中文回答问题。"
            )
            messages.append({
                "role": "system",
                "content": system_prompt
            })

            # 添加对话上下文（智能截断，保留最近的对话）
            max_context = kwargs.get('max_context', 10)
            if context:
                recent_context = context[-max_context:] if len(context) > max_context else context
                for msg in recent_context:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if content and content.strip():
                        messages.append({
                            "role": role,
                            "content": content
                        })

            # 添加当前用户消息
            messages.append({
                "role": "user",
                "content": prompt
            })

            print(f"🤖 调用 DeepSeek API")
            print(f"   - 消息数量: {len(messages)}")
            print(f"   - 用户输入: {prompt[: 50]}{'...' if len(prompt) > 50 else ''}")

            # 准备 API 调用参数（支持动态覆盖）
            api_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                "top_p": kwargs.get('top_p', self.top_p),
                "frequency_penalty": kwargs.get('frequency_penalty', self.frequency_penalty),
                "presence_penalty": kwargs.get('presence_penalty', self.presence_penalty),
                "stream": False
            }

            # 调用 DeepSeek API
            response = self.client.chat.completions.create(**api_params)

            # 提取AI回复
            reply = response.choices[0].message.content

            if not reply or not reply.strip():
                raise AIException("AI回复为空")

            # 统计信息
            usage = response.usage
            print(f"✅ AI回复成功")
            print(f"   - 回复长度: {len(reply)} 字符")
            print(
                f"   - Token 使用: 输入 {usage.prompt_tokens}, 输出 {usage.completion_tokens}, 总计 {usage.total_tokens}")

            return reply.strip()

        except ValidationException:
            raise
        except Exception as e:
            # 详细的错误分类和处理
            error_msg = str(e).lower()

            if "api_key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
                raise AIException("API密钥无效或未授权，请检查 DEEPSEEK_API_KEY 配置")
            elif "rate_limit" in error_msg or "429" in error_msg:
                raise AIException("API调用频率超限，请稍后再试")
            elif "timeout" in error_msg:
                raise AIException("API调用超时，请检查网络连接或重试")
            elif "connection" in error_msg or "network" in error_msg:
                raise AIException("网络连接失败，请检查能否访问 api.deepseek.com")
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise AIException("DeepSeek服务暂时不可用，请稍后重试")
            else:
                print(f"❌ AI调用失败: {str(e)}")
                raise AIException(f"生成AI回复失败: {str(e)}")

    def generate_reply_with_context(
            self,
            prompt: str,
            context: List[Dict[str, Any]],
            max_tokens: int = 2000
    ) -> str:
        """
        基于上下文生成AI回复（便捷方法）

        Args:
            prompt: 用户当前输入
            context: 对话历史上下文
            max_tokens: 最大令牌数

        Returns:
            AI回复内容
        """
        return self.generate_reply(
            prompt=prompt,
            context=context,
            max_tokens=max_tokens
        )

    def process_chat_generate_request(self, request: ChatGenerateRequest) -> Dict[str, Any]:
        """
        处理AI生成请求（无上下文）

        Args:
            request: AI生成请求数据

        Returns:
            包含AI回复的字典
        """
        try:
            reply = self.generate_reply(request.prompt)

            return {
                "reply": reply,
                "timestamp": datetime.utcnow().isoformat(),
                "model": self.model
            }

        except Exception as e:
            raise AIException(f"处理AI生成请求失败: {str(e)}")

    def process_chat_with_context(
            self,
            user_message: Dict[str, Any],
            context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        基于上下文处理聊天（带历史记录）

        Args:
            user_message: 用户消息
            context: 对话上下文

        Returns:
            包含AI回复的字典
        """
        try:
            prompt = user_message.get("content", "")
            reply = self.generate_reply_with_context(prompt, context)

            return {
                "reply": reply,
                "timestamp": datetime.utcnow().isoformat(),
                "model": self.model,
                "context_used": len(context)
            }

        except Exception as e:
            raise AIException(f"基于上下文处理聊天失败: {str(e)}")

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 Token 数量（用于上下文管理）

        Args:
            text: 输入文本

        Returns:
            估算的 Token 数量
        """
        # 简单估算：中文 1 字符 ≈ 1 token，英文 1 单词 ≈ 1 token
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return chinese_chars + int(other_chars * 0.25)

    def __del__(self):
        """清理资源（优雅关闭连接）"""
        try:
            if hasattr(self, 'client') and hasattr(self.client, '_client'):
                if hasattr(self.client._client, 'close'):
                    self.client._client.close()
                    print("🔒 AI服务连接已关闭")
        except Exception:
            pass  # 静默处理清理错误