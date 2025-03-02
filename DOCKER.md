# ARCP论文讨论班 - Docker部署指南

本文档提供使用Docker部署ARCP论文讨论班系统的详细步骤。

## 前置条件

1. 安装Docker和Docker Compose：
   - [Docker安装指南](https://docs.docker.com/get-docker/)
   - [Docker Compose安装指南](https://docs.docker.com/compose/install/)

2. 确保以下端口未被占用：
   - 5000：Web服务端口

## 部署步骤

### 1. 准备环境变量

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

### 2. 使用Docker Compose启动服务

```bash
docker-compose up -d
```

此命令将：
- 构建Docker镜像
- 创建并启动容器
- 初始化数据库（如果是首次运行）
- 在后台运行服务

### 3. 访问系统

启动成功后，通过浏览器访问：

```
http://localhost:5000
```

初始管理员账号：
- 用户名：admin
- 密码：admin

**重要：** 首次登录后请立即修改管理员密码！

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

## 数据持久化

系统数据保存在`./data`目录下，包括：
- SQLite数据库文件

如需备份数据，只需复制`data`目录即可。

## 系统升级

升级系统时，执行以下步骤：

```bash
# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose down
docker-compose up -d --build
```

## 生产环境建议

1. 使用HTTPS保护您的网站
2. 更改默认管理员密码
3. 定期备份数据目录
4. 配置防火墙，只开放必要端口

## 常见问题

1. 如果遇到权限问题，请检查`data`目录的权限
2. 如果邮件发送失败，请检查邮件服务器配置
3. 如果容器无法启动，请查看日志以获取详细错误信息 
