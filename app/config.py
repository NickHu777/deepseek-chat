# app/config.py
"""
配置管理模块
作用：统一管理应用配置，根据环境自动切换
开发逻辑：创建单例配置类，避免重复读取环境变量
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载.env文件
# 注意：生产环境不会使用.env文件，而是使用docker-compose.yml中的环境变量
load_dotenv()


class Settings:
    """配置类，使用单例模式确保配置一致"""

    # 应用配置
    ENV: str = "development"  # 默认开发环境
    DEBUG: bool = True

    # 数据库配置 - 默认值
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_NAME: str = "chat_dev"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # API配置
    DEEPSEEK_API_KEY: Optional[str] = None

    def __init__(self):
        """初始化配置，从环境变量覆盖默认值"""
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 环境类型
        self.ENV = os.getenv("ENV", self.ENV)

        # 根据环境自动切换数据库配置
        if self.ENV == "production":
            # 生产环境配置
            self.DB_HOST = os.getenv("DB_HOST", "postgres")  # 注意：容器内使用服务名
            self.DB_PORT = int(os.getenv("DB_PORT", 5432))
            self.DB_NAME = os.getenv("DB_NAME", "chat_db")
            self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        else:
            # 开发环境配置
            self.DB_HOST = os.getenv("DB_HOST", self.DB_HOST)
            self.DB_PORT = int(os.getenv("DB_PORT", self.DB_PORT))
            self.DB_NAME = os.getenv("DB_NAME", self.DB_NAME)
            self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"

        # 通用配置（所有环境）
        self.DB_USER = os.getenv("DB_USER", self.DB_USER)
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", self.DB_PASSWORD)
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def __str__(self) -> str:
        """安全地显示配置信息（隐藏敏感信息）"""
        return (
            f"Settings(ENV={self.ENV}, DB_HOST={self.DB_HOST}, "
            f"DB_PORT={self.DB_PORT}, DB_NAME={self.DB_NAME}, "
            f"DEBUG={self.DEBUG})"
        )


# 创建全局配置实例
# 这是单例模式的应用：整个应用共享同一个配置实例
settings = Settings()