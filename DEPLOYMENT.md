# 论文讲解安排系统部署指南

本文档提供将论文讲解安排系统部署到生产环境的步骤。

## 部署前准备

1. 一台运行Linux/Windows的服务器
2. Python 3.8+
3. 邮件服务器账号信息

## 部署步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

将`.env.example`复制为`.env`并编辑其中的配置：

```bash
cp .env.example .env
```

编辑`.env`文件，填入您的实际配置：

```
SECRET_KEY=生成一个安全的随机密钥
MAIL_SERVER=您的邮件服务器地址
MAIL_PORT=邮件服务器端口
MAIL_USERNAME=邮箱用户名
MAIL_PASSWORD=邮箱密码
MAIL_DEFAULT_SENDER=发件人邮箱
```

### 3. 初始化数据库

```bash
flask db-init
```

### 4. 使用Gunicorn部署（Linux）

安装Gunicorn:

```bash
pip install gunicorn
```

启动应用:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### 5. 使用Waitress部署（Windows）

安装Waitress:

```bash
pip install waitress
```

创建`run.py`:

```python
from waitress import serve
from app import app

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
```

启动应用:

```bash
python run.py
```

### 6. 配置Nginx（推荐）

安装Nginx并配置反向代理:

```nginx
server {
    listen 80;
    server_name your_domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. 使用Systemd管理服务（Linux）

创建服务文件`/etc/systemd/system/paper-schedule.service`:

```
[Unit]
Description=Paper Schedule System
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/your/app
ExecStart=/path/to/your/python/env/bin/gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务:

```bash
sudo systemctl enable paper-schedule
sudo systemctl start paper-schedule
```

## 安全建议

1. 使用HTTPS保护您的网站
2. 定期更新管理员密码
3. 限制服务器访问，使用防火墙
4. 定期备份数据库

## 故障排除

如果遇到问题，请检查:

1. 应用日志
2. 确保数据库权限正确
3. 确保邮件服务器配置正确
4. 确保防火墙允许相关端口访问 
