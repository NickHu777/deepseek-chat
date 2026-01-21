-- 数据库初始化脚本
-- 在容器首次启动时执行

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 设置搜索路径（可选）
SET search_path TO public;

-- 创建其他数据库对象可以在这里添加
-- 例如：创建自定义类型、函数等

-- 注意：表结构将由SQLAlchemy自动创建
-- 所以这里主要创建一些Alchemy无法自动创建的对象

-- 示例：创建一个用于审计的日志表（如果需要）
-- CREATE TABLE IF NOT EXISTS audit_log (
--     id SERIAL PRIMARY KEY,
--     action VARCHAR(50),
--     table_name VARCHAR(50),
--     record_id INTEGER,
--     changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 添加注释
COMMENT ON DATABASE chat_dev IS 'DeepSeek聊天项目开发数据库';
