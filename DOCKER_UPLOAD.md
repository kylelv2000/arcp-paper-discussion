# ARCP论文讨论班 - Docker镜像构建与上传指南

本文档提供如何构建ARCP论文讨论班系统的Docker镜像并上传到Docker Hub或私有仓库的详细步骤。

## 构建Docker镜像

### 本地构建

在项目根目录执行以下命令构建Docker镜像：

```bash
docker build -t arcp-paper-discussion:latest .
```

构建完成后，您可以通过以下命令验证镜像是否创建成功：

```bash
docker images
```

应该能看到名为`arcp-paper-discussion`的镜像。

## 推送到Docker Hub

### 1. 登录Docker Hub

首先，您需要登录到Docker Hub：

```bash
docker login
```

系统会提示您输入Docker Hub的用户名和密码。

### 2. 标记镜像

为您的镜像添加标签，格式为`用户名/镜像名:标签`：

```bash
docker tag arcp-paper-discussion:latest 您的用户名/arcp-paper-discussion:latest
```

### 3. 推送镜像

将标记的镜像推送到Docker Hub：

```bash
docker push 您的用户名/arcp-paper-discussion:latest
```

## 推送到私有Docker仓库

### 1. 登录私有仓库

```bash
docker login 私有仓库地址
```

### 2. 标记镜像

```bash
docker tag arcp-paper-discussion:latest 私有仓库地址/arcp-paper-discussion:latest
```

### 3. 推送镜像

```bash
docker push 私有仓库地址/arcp-paper-discussion:latest
```

## 使用推送的镜像

### 从Docker Hub拉取

```bash
docker pull 您的用户名/arcp-paper-discussion:latest
```

### 从私有仓库拉取

```bash
docker pull 私有仓库地址/arcp-paper-discussion:latest
```

### 运行容器

```bash
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data --env-file .env --name arcp-paper-discussion 您的用户名/arcp-paper-discussion:latest
```

## 使用GitHub Actions自动构建和推送

您可以设置GitHub Actions工作流自动构建和推送Docker镜像。

在项目根目录创建`.github/workflows/docker-build.yml`文件：

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

注意：您需要在GitHub仓库设置中添加`DOCKERHUB_USERNAME`和`DOCKERHUB_TOKEN`作为secrets。

## 多架构镜像构建（ARM64/AMD64）

如果您需要同时支持多种硬件架构，可以使用以下命令构建多架构镜像：

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t 您的用户名/arcp-paper-discussion:latest --push .
```

这将创建同时支持Intel/AMD处理器和ARM处理器的Docker镜像。 
