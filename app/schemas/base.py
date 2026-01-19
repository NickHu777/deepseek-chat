# app/schemas/base.py
"""
基础模式定义
作用：避免循环导入问题，定义所有模式共享的基础类
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """所有模式的基类"""
    model_config = ConfigDict(
        from_attributes=True,    # 允许从ORM对象转换（SQLAlchemy模型）
        populate_by_name=True,   # 允许使用字段别名
        str_strip_whitespace=True,  # 自动去除字符串空格
    )


class TimestampSchema(BaseSchema):
    """包含时间戳的基类"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None