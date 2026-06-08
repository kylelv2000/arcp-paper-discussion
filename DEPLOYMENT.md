# ARCP论文讨论班 - 部署指南

本文档汇总了 ARCP 论文讨论班系统的部署方式，包括**传统部署**、**Docker 部署**以及 **Docker 镜像构建与上传**。

## 目录

- [一、传统部署](#一传统部署)
- [二、Docker 部署](#二docker-部署)
- [三、Docker 镜像构建与上传](#三docker-镜像构建与上传)

---

## 一、传统部署

### 部署前准备

1. 一台运行 Linux/Windows 的服务器
2. Python 3.8+
3. 邮件服务器账号信息

### 1. 安装 uv 并同步依赖

首先在服务器上安装 `uv`（Ruff 团队的超高速包管理器），然后一键同步项目依赖：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

### 2. 配置环境变量

将 `.env.example` 复制为 `.env` 并编辑其中的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的实际配置：

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
uv run flask db-init
```

### 4. 使用 Gunicorn 部署（Linux）

可以通过 `uv` 安装 Gunicorn 并运行项目：

```bash
uv pip install gunicorn
```

启动应用：

```bash
uv run gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
```

### 5. 使用 Waitress 部署（Windows）

Waitress 已包含在项目依赖中，直接启动 [wsgi.py](wsgi.py) 即可：

```bash
uv run python wsgi.py
```

### 6. 配置 Nginx（推荐）

安装 Nginx 并配置反向代理：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. 使用 Systemd 管理服务（Linux）

创建服务文件 `/etc/systemd/system/paper-schedule.service`：

```ini
[Unit]
Description=Paper Schedule System
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/your/app
ExecStart=/path/to/your/app/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl enable paper-schedule
sudo systemctl start paper-schedule
```

### 故障排除

如果遇到问题，请检查：

1. 应用日志
2. 确保数据库权限正确
3. 确保邮件服务器配置正确
4. 确保防火墙允许相关端口访问

---

## 二、Docker 部署

### 前置条件

1. 安装 Docker 和 Docker Compose：
   - [Docker 安装指南](https://docs.docker.com/get-docker/)
   - [Docker Compose 安装指南](https://docs.docker.com/compose/install/)

2. 确保以下端口未被占用：
   - 5001：Web 服务端口

### 1. 准备环境变量

将 `.env.example` 复制为 `.env` 并编辑其中的配置：

```bash
cp .env.example .env
```

填入您的实际配置（同上文的环境变量说明）。

### 2. 使用 Docker Compose 启动服务

```bash
docker-compose up -d
```

此命令将：

- 构建 Docker 镜像
- 创建并启动容器
- 初始化数据库（如果是首次运行）
- 在后台运行服务

### 3. 访问系统

启动成功后，通过浏览器访问：

```
http://localhost:5001
```

初始管理员账号：

- 用户名：admin
- 密码：admin

**重要：** 首次登录后请立即修改管理员密码！（参见 README 的安全指南）

### 4. 管理容器

查看日志：

```bash
docker-compose logs -f
```

停止服务：

```bash
docker-compose down
```

重新启动服务：

```bash
docker-compose restart
```

### 数据持久化

系统数据保存在 `./instance` 目录下（与本地运行一致），包括 SQLite 数据库文件。如需备份数据，只需复制 `instance` 目录即可。

### 系统升级

```bash
# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose down
docker-compose up -d --build
```

### 常见问题

1. 如果遇到权限问题，请检查 `instance` 目录的权限
2. 如果邮件发送失败，请检查邮件服务器配置
3. 如果容器无法启动，请查看日志以获取详细错误信息

---

## 三、Docker 镜像构建与上传

### 构建 Docker 镜像

在项目根目录执行以下命令构建 Docker 镜像：

```bash
docker build -t arcp-paper-discussion:latest .
```

构建完成后，可以通过以下命令验证镜像是否创建成功：

```bash
docker images
```

应该能看到名为 `arcp-paper-discussion` 的镜像。

### 推送到 Docker Hub

1. 登录 Docker Hub：

   ```bash
   docker login
   ```

2. 标记镜像（格式为 `用户名/镜像名:标签`）：

   ```bash
   docker tag arcp-paper-discussion:latest 您的用户名/arcp-paper-discussion:latest
   ```

3. 推送镜像：

   ```bash
   docker push 您的用户名/arcp-paper-discussion:latest
   ```

### 推送到私有 Docker 仓库

```bash
docker login 私有仓库地址
docker tag arcp-paper-discussion:latest 私有仓库地址/arcp-paper-discussion:latest
docker push 私有仓库地址/arcp-paper-discussion:latest
```

### 使用推送的镜像

```bash
# 从 Docker Hub 拉取
docker pull 您的用户名/arcp-paper-discussion:latest

# 运行容器
docker run -d -p 5001:5001 -v $(pwd)/instance:/app/instance --env-file .env --name arcp-paper-discussion 您的用户名/arcp-paper-discussion:latest
```

### 使用 GitHub Actions 自动构建和推送

在项目根目录创建 `.github/workflows/docker-build.yml` 文件：

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1

      - name: Login to DockerHub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: |
            您的用户名/arcp-paper-discussion:latest
            您的用户名/arcp-paper-discussion:${{ github.ref_name }}
```

注意：您需要在 GitHub 仓库设置中添加 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` 作为 secrets。

### 多架构镜像构建（ARM64/AMD64）

如果需要同时支持多种硬件架构：

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t 您的用户名/arcp-paper-discussion:latest --push .
```

这将创建同时支持 Intel/AMD 处理器和 ARM 处理器的 Docker 镜像。
