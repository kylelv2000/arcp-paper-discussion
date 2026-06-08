FROM python:3.10-slim

# 从官方镜像拷贝 uv 二进制
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 拷贝依赖配置文件以进行依赖预安装
COPY pyproject.toml uv.lock ./

# 安装项目依赖（使用 --system 直接安装到容器系统环境）
RUN uv pip install --system --no-cache .

# 拷贝项目文件
COPY . .

# 创建数据目录（与本地设计一致，统一使用 instance 目录）
RUN mkdir -p /app/instance

# 设置环境变量
ENV FLASK_APP=wsgi.py
ENV PYTHONUNBUFFERED=1

# 转换行尾符并赋予执行权限
RUN sed -i 's/\r$//' /app/scripts/docker_entrypoint.sh && chmod +x /app/scripts/docker_entrypoint.sh

# 暴露端口
EXPOSE 5001

# 使用入口脚本
ENTRYPOINT ["/app/scripts/docker_entrypoint.sh"]

 
