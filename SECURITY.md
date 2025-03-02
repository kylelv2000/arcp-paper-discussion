# 论文讲解安排系统安全指南

本文档提供了加强系统安全性的建议和最佳实践。

## 1. 身份验证安全

### 更改默认管理员密码

系统初始化时创建了一个默认管理员账户（用户名：admin，密码：admin）。务必在首次登录后立即更改密码。

要更改管理员密码，可以登录后手动编辑数据库，或使用以下Python脚本：

```python
from app import db, User
import os
from werkzeug.security import generate_password_hash
from getpass import getpass

# 获取管理员用户
admin = User.query.filter_by(username='admin').first()
if admin:
    # 输入新密码
    new_password = getpass('请输入新密码: ')
    confirm_password = getpass('请再次输入新密码: ')
    
    if new_password == confirm_password:
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print('密码已更新')
    else:
        print('两次输入的密码不一致')
else:
    print('未找到管理员账户')
```

将此内容保存为`change_password.py`，然后运行它：

```bash
python change_password.py
```

### 添加更多管理员账户

可以考虑增加更多管理员账户，并为不同的人员分配不同的管理员账户：

```python
from app import db, User

new_admin = User(username='new_admin_name', is_admin=True)
new_admin.set_password('secure_password')
db.session.add(new_admin)
db.session.commit()
```

## 2. Web应用安全

### 启用HTTPS

强烈建议使用HTTPS保护您的网站。可以通过以下方式实现：

1. 获取SSL证书（可以使用Let's Encrypt免费获取）
2. 配置Nginx或其他反向代理服务器以使用SSL证书

### 设置安全headers

在Nginx配置中添加以下安全headers：

```nginx
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options SAMEORIGIN;
add_header X-XSS-Protection "1; mode=block";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:;";
```

## 3. 服务器安全

### 限制端口访问

确保只开放必要的端口，例如80（HTTP）和443（HTTPS）：

```bash
# 使用UFW（Ubuntu防火墙）
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 定期更新服务器

确保定期更新服务器操作系统和所有软件包：

```bash
# 对于Ubuntu/Debian
sudo apt update
sudo apt upgrade

# 对于CentOS/RHEL
sudo yum update
```

## 4. 数据安全

### 数据库备份

定期备份数据库：

```bash
# 设置定时任务，每天凌晨2点备份
0 2 * * * sqlite3 /path/to/your/app/paper_schedule.db .dump > /path/to/backup/paper_schedule_$(date +\%Y\%m\%d).sql
```

### 数据加密

确保敏感数据（如密码）已加密存储。本系统已使用Werkzeug的password_hash函数加密存储密码。

## 5. 日志和监控

### 启用应用日志

修改应用配置以记录详细的日志：

```python
import logging
from logging.handlers import RotatingFileHandler

# 在app.py中添加
if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=False)
```

### 设置入侵检测

考虑安装入侵检测系统如Fail2ban，限制暴力攻击：

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 联系方式

如果您发现任何安全漏洞，请立即联系系统管理员。 
