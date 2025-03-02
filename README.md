# ARCP论文讨论班

一个简单的论文讲解安排网站，允许用户查看、编辑论文讲解安排，并支持邮件通知功能。

## 功能

- 查看和编辑论文讲解安排表
- 管理员后台管理
- 邮件通知功能（可设置提前通知时间）
- 安全的用户认证

## 安装和运行

1. 安装依赖:
```
pip install -r requirements.txt
```

2. 配置环境变量（创建.env文件，包含以下内容）:
```
SECRET_KEY=your_secret_key
MAIL_SERVER=your_mail_server
MAIL_PORT=your_mail_port
MAIL_USERNAME=your_mail_username
MAIL_PASSWORD=your_mail_password
MAIL_DEFAULT_SENDER=your_default_sender_email
```

3. 初始化数据库:
```
flask db-init
```

4. 运行应用:
```
flask run
```

## 访问网站

- 主页: http://localhost:5000/
- 管理员登录: http://localhost:5000/admin/login 
