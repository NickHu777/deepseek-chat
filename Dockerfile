# Dockerfile
# 构建生产环境的 FastAPI 应用镜像

# 第一阶段：构建依赖
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local

# 确保 Python 可以找到用户安装的包
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# 复制应用代码
COPY ./app ./app

# 🔥 注释掉这两行（学习项目不需要非 root 用户）
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令 - 添加超时配置支持长文本AI回复
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]