FROM python:3.9-slim

WORKDIR /app

# 拷贝项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 添加waitress到依赖中
RUN pip install --no-cache-dir waitress

# 设置环境变量
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 转换行尾符并赋予执行权限
RUN sed -i 's/\r$//' /app/docker_entrypoint.sh && chmod +x /app/docker_entrypoint.sh

# 暴露端口
EXPOSE 5000

# 使用入口脚本
ENTRYPOINT ["/app/docker_entrypoint.sh"] 
