# app/models/__init__.py
"""
模型包初始化文件 - 修复版
作用：集中导入所有模型和数据库基础类
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship, validates
import enum

# 导入数据库基础类（关键修复！）
from app.database import Base  # 从 database.py 导入 Base

# 导入基类
from app.models.base import BaseModel

# 导入枚举
from app.models.chat_message import SenderType

# 导入模型
from app.models.chat_history import ChatHistory
from app.models.chat_message import ChatMessage

# 方便导入的列表 - 添加 Base
__all__ = [
    "Base",           # SQLAlchemy declarative_base
    "BaseModel",      # 自定义基础模型
    "SenderType",     # 发送者类型枚举
    "ChatHistory",    # 聊天历史模型
    "ChatMessage",    # 聊天消息模型
]