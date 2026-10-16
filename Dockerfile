# =========================================================
# 智服云 CoreDesk - Docker 生产部署镜像
# =========================================================
FROM python:3.11-slim

# 设置工作目录与环境变量
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    PORT=8000 \
    HOST=0.0.0.0

# 安装系统基础依赖（时区、curl 健康检测）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 库
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制系统源码
COPY app ./app
COPY run.py .

# 暴露端口
EXPOSE 8000

# 容器健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/system/mode || exit 1

# 启动服务 (生产环境推荐 4 工作进程 Uvicorn 或 run.py)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
