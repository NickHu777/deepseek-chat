# app/database.py
"""
数据库连接模块 - 修复版
"""

from sqlalchemy import create_engine, text  # 新增：导入text函数
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 1. 创建数据库引擎（保持不变）
engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# 2. 创建会话工厂（保持不变）
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 3. 创建基类（保持不变）
Base = declarative_base()


# 4. 数据库会话依赖函数（保持不变）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 5. 修复数据库连接测试函数
def test_connection():
    """测试数据库连接是否正常"""
    try:
        # 创建临时会话
        db = SessionLocal()

        # 使用text()包装SQL语句 - 这是SQLAlchemy 2.0的要求
        # 为什么需要text()？防止SQL注入，明确表明这是SQL文本
        result = db.execute(text("SELECT 1"))

        # 获取结果
        row = result.fetchone()
        db.close()

        if row and row[0] == 1:
            print("✅ 数据库连接成功")
            return True
        else:
            print("❌ 数据库查询结果异常")
            return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


# 6. 模型导入占位符
# 这里先声明，实际模型将在models模块中定义
__all__ = ["Base", "engine", "SessionLocal", "get_db", "test_connection"]