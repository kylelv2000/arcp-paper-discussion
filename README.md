# ARCP论文讨论班

一个简单的论文讲解安排网站，允许用户查看、编辑论文讲解安排，并支持邮件通知功能。

## 功能

- 查看和编辑论文讲解安排表
- 管理员后台管理
- 邮件通知功能（可设置提前通知时间）
- 安全的用户认证

## 安装和运行

本项目使用现代化的 `uv` 进行依赖和项目管理，已废除传统的 `pip` 方式。

### 安装及运行步骤

1. **一键启动（推荐：最快最省心）**：

   ```bash
   uv run python scripts/start.py
   ```

   *该命令会自动在本地虚拟环境中同步依赖、自动初始化数据库并在浏览器中运行项目。*

2. **手动分步安装**：

   ```bash
   uv venv
   source .venv/bin/activate  # macOS/Linux (Windows 使用 .venv\Scripts\activate)
   uv sync
   ```

3. **配置环境变量**（创建 `.env` 文件，包含以下内容）：

   ```
   SECRET_KEY=your_secret_key
   MAIL_SERVER=your_mail_server
   MAIL_PORT=your_mail_port
   MAIL_USERNAME=your_mail_username
   MAIL_PASSWORD=your_mail_password
   MAIL_DEFAULT_SENDER=your_default_sender_email
   ```

4. **初始化数据库**：

   ```bash
   uv run flask db-init
   ```

5. **运行应用**：

   ```bash
   uv run flask run --port 5001
   ```

## 访问网站

- 主页: http://localhost:5001/
- 管理员登录: http://localhost:5001/admin/login

> 部署到生产环境（传统部署 / Docker / 镜像构建上传）请参阅 [DEPLOYMENT.md](DEPLOYMENT.md)。

---

## 安全指南

本节提供加强系统安全性的建议和最佳实践。

### 1. 身份验证安全

#### 更改默认管理员密码

系统初始化时会创建一个默认管理员账户（用户名：`admin`，密码：`admin`）。**务必在首次登录后立即更改密码。**

项目内置了交互式改密命令，直接运行即可：

```bash
uv run flask change-password
```

按提示输入新密码（长度至少 8 个字符）即可完成更新。

#### 添加更多管理员账户

可以为不同人员分配不同的管理员账户。通过 `flask shell` 创建：

```python
from arcp.extensions import db
from arcp.models import User

new_admin = User(username='new_admin_name', is_admin=True)
new_admin.set_password('secure_password')
db.session.add(new_admin)
db.session.commit()
```

### 2. Web 应用安全

#### 启用 HTTPS

强烈建议使用 HTTPS 保护您的网站：

1. 获取 SSL 证书（可使用 Let's Encrypt 免费获取）
2. 配置 Nginx 或其他反向代理服务器以使用 SSL 证书

#### 设置安全 headers

在 Nginx 配置中添加以下安全 headers：

```nginx
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options SAMEORIGIN;
add_header X-XSS-Protection "1; mode=block";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:;";
```

### 3. 服务器安全

#### 限制端口访问

确保只开放必要的端口，例如 80（HTTP）和 443（HTTPS）：

```bash
# 使用 UFW（Ubuntu 防火墙）
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

#### 定期更新服务器

```bash
# 对于 Ubuntu/Debian
sudo apt update && sudo apt upgrade

# 对于 CentOS/RHEL
sudo yum update
```

### 4. 数据安全

#### 数据库备份

定期备份数据库：

```bash
# 设置定时任务，每天凌晨 2 点备份
0 2 * * * sqlite3 /path/to/your/app/paper_schedule.db .dump > /path/to/backup/paper_schedule_$(date +\%Y\%m\%d).sql
```

#### 数据加密

确保敏感数据（如密码）已加密存储。本系统已使用 Werkzeug 的 `password_hash` 函数加密存储密码。

### 5. 日志和监控

#### 设置入侵检测

考虑安装入侵检测系统如 Fail2ban，限制暴力攻击：

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 报告安全漏洞

如果您发现任何安全漏洞，请立即联系系统管理员。
