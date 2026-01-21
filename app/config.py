# app/config.py
"""
配置管理模块
作用：统一管理应用配置，根据环境自动切换
开发逻辑：创建单例配置类，避免重复读取环境变量
现在扩展：添加向量化功能所需配置
"""

import os
from typing import Optional, List
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

    # ============ 向量化功能新增配置 ============

    # 向量模型配置
    VECTOR_MODEL: str = "all-MiniLM-L6-v2"  # 默认向量模型
    EMBEDDING_DIMENSION: int = 384  # 向量维度

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"  # 文件上传目录
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB，单位：字节
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf",  # PDF文档
        ".docx", ".doc",  # Word文档
        ".txt", ".md",  # 文本文件
        ".csv", ".xlsx", ".xls",  # Excel文件
        ".json",  # JSON文件
    ]

    # 文本处理配置
    CHUNK_SIZE: int = 1000  # 文本分块大小（字符数）
    CHUNK_OVERLAP: int = 200  # 分块重叠大小（字符数）

    # 向量搜索配置
    SIMILARITY_THRESHOLD: float = 0.7  # 相似度阈值（0-1之间）
    SEARCH_LIMIT: int = 5  # 默认搜索返回数量

    # 处理配置
    ENABLE_ASYNC_PROCESSING: bool = True  # 是否启用异步处理

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

        # ============ 加载向量相关配置 ============

        # 向量模型配置
        self.VECTOR_MODEL = os.getenv("VECTOR_MODEL", self.VECTOR_MODEL)

        # 向量维度（需要转换为整数）
        embedding_dim_str = os.getenv("EMBEDDING_DIMENSION")
        if embedding_dim_str is not None:
            self.EMBEDDING_DIMENSION = int(embedding_dim_str)

        # 文件上传配置
        self.UPLOAD_DIR = os.getenv("UPLOAD_DIR", self.UPLOAD_DIR)

        # 最大文件大小（需要转换为整数）
        max_size_str = os.getenv("MAX_FILE_SIZE")
        if max_size_str is not None:
            self.MAX_FILE_SIZE = int(max_size_str)

        # 允许的文件扩展名（从字符串解析为列表）
        extensions_str = os.getenv("ALLOWED_EXTENSIONS")
        if extensions_str is not None:
            # 支持格式：".pdf,.docx,.txt" 或 "pdf,docx,txt"
            extensions = extensions_str.split(",")
            self.ALLOWED_EXTENSIONS = [
                ext if ext.startswith(".") else f".{ext}"
                for ext in extensions
            ]

        # 文本处理配置
        chunk_size_str = os.getenv("CHUNK_SIZE")
        if chunk_size_str is not None:
            self.CHUNK_SIZE = int(chunk_size_str)

        chunk_overlap_str = os.getenv("CHUNK_OVERLAP")
        if chunk_overlap_str is not None:
            self.CHUNK_OVERLAP = int(chunk_overlap_str)

        # 向量搜索配置
        threshold_str = os.getenv("SIMILARITY_THRESHOLD")
        if threshold_str is not None:
            self.SIMILARITY_THRESHOLD = float(threshold_str)

        limit_str = os.getenv("SEARCH_LIMIT")
        if limit_str is not None:
            self.SEARCH_LIMIT = int(limit_str)

        # 处理配置
        async_str = os.getenv("ENABLE_ASYNC_PROCESSING")
        if async_str is not None:
            self.ENABLE_ASYNC_PROCESSING = async_str.lower() == "true"

    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ============ 新增实用方法 ============

    @property
    def upload_path(self) -> str:
        """获取完整的文件上传路径"""
        # 确保上传目录存在
        if not os.path.exists(self.UPLOAD_DIR):
            os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return os.path.abspath(self.UPLOAD_DIR)

    def is_file_allowed(self, filename: str) -> bool:
        """检查文件类型是否允许上传"""
        # 获取文件扩展名并转换为小写
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in self.ALLOWED_EXTENSIONS

    @property
    def max_file_size_mb(self) -> float:
        """以MB为单位返回最大文件大小"""
        return self.MAX_FILE_SIZE / (1024 * 1024)

    def get_allowed_extensions_str(self) -> str:
        """获取允许的文件扩展名字符串（用于显示）"""
        return ", ".join(self.ALLOWED_EXTENSIONS)

    def __str__(self) -> str:
        """安全地显示配置信息（隐藏敏感信息）"""
        config_str = (
            f"Settings(ENV={self.ENV}, DB_HOST={self.DB_HOST}, "
            f"DB_PORT={self.DB_PORT}, DB_NAME={self.DB_NAME}, "
            f"DEBUG={self.DEBUG}, "
        )

        # 添加向量配置信息
        vector_config_str = (
            f"VECTOR_MODEL={self.VECTOR_MODEL}, "
            f"UPLOAD_DIR={self.UPLOAD_DIR}, "
            f"MAX_FILE_SIZE={self.MAX_FILE_SIZE}, "
            f"ALLOWED_EXTENSIONS={self.get_allowed_extensions_str()}, "
            f"CHUNK_SIZE={self.CHUNK_SIZE}, "
            f"CHUNK_OVERLAP={self.CHUNK_OVERLAP}, "  # 新增这一行
            f"SIMILARITY_THRESHOLD={self.SIMILARITY_THRESHOLD}, "
            f"SEARCH_LIMIT={self.SEARCH_LIMIT})"  # 新增这一行
        )

        return config_str + vector_config_str


# 创建全局配置实例
# 这是单例模式的应用：整个应用共享同一个配置实例
settings = Settings()