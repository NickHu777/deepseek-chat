# app/models/base.py
"""
SQLAlchemy 模型基类
作用：定义所有模型共享的字段和方法
开发逻辑：创建可复用的基类，避免重复代码
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from app.database import Base


class BaseModel(Base):
    """所有模型的抽象基类"""
    __abstract__ = True  # 不创建表

    # 通用字段
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        """友好的对象表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self):
        """将模型转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result