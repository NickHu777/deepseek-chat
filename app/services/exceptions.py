"""
异常定义 - 完整版
包含所有服务需要的异常类
"""

class ServiceException(Exception):
    """服务层基础异常"""
    pass

class NotFoundException(ServiceException):
    """资源未找到异常"""
    def __init__(self, resource: str, resource_id):
        message = f"{resource} ID {resource_id} 未找到"
        super().__init__(message)

class ValidationException(ServiceException):
    """数据验证异常"""
    pass

class DatabaseException(ServiceException):
    """数据库操作异常"""
    pass

class AIException(ServiceException):
    """AI服务异常"""
    pass
