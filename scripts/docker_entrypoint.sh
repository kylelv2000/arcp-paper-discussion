#!/bin/bash

# 创建数据目录
mkdir -p /app/instance

# 初始化数据库（如果不存在）
if [ ! -f /app/instance/paper_schedule.db ]; then
    echo "正在初始化数据库..."
    flask db-init
else
    echo "数据库已存在，跳过初始化..."
fi

# 启动服务
echo "正在启动ARCP论文讨论班..."
waitress-serve --host=0.0.0.0 --port=5001 wsgi:app
 
