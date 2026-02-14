# TOTP Auth System

基于 TOTP 动态密码的账号管理与登录系统 Demo

## 功能特点

- **无密码登录**：使用 TOTP 动态密码，无需短信/邮件验证
- **账号管理**：超级管理员可创建、禁用账号
- **TOTP 管理**：支持密钥轮换和 QR Code 生成
- **JWT 认证**：Access Token + Refresh Token
- **Redis 黑名单**：确保注销后 Token 立即失效
- **美观界面**：响应式设计，用户友好

## 技术栈

- Python 3.12
- FastAPI
- PostgreSQL
- Redis
- TOTP (RFC 6238)
- JWT
- Jinja2
- Docker + Docker Compose

## 快速开始

### 1. 克隆仓库

```bash
git clone <repository-url>
cd totp_auth_system
```

### 2. 启动服务

使用 Docker Compose 启动所有服务：

```bash
docker compose up -d --build
```

服务将在以下地址运行：
- **Web 服务**：http://localhost:8000
- **PostgreSQL**：localhost:5432
- **Redis**：localhost:6379

### 3. 初始化超级管理员

服务启动时会自动初始化超级管理员账号：
- **用户名**：admin
- **角色**：super_admin

查看日志获取 QR Code 信息：

```bash
docker logs totp_demo_web
```

### 4. 登录系统

1. 打开 http://localhost:8000/login
2. 使用 Authenticator App 扫描 QR Code 添加账号
3. 输入用户名和动态密码登录

## 页面说明

### 登录页 (`/login`)
- 账号 + TOTP 动态密码登录

### 管理后台 (`/admin`)
- **用户列表**：显示所有用户信息
- **创建用户**：输入用户名创建新账号
- **禁用用户**：点击删除按钮确认后禁用

### 用户中心 (`/user`)
- **Rotate TOTP Secret**：重新生成密钥并获取新 QR Code
- **Generate QR Code**：使用当前密钥生成 QR Code

## API 接口

### 认证相关
- `POST /auth/login`：登录
- `POST /auth/logout`：注销

### 管理相关
- `POST /admin/users`：创建用户
- `POST /admin/users/{id}/disable`：禁用用户

### 用户相关
- `POST /user/totp/rotate`：轮换 TOTP 密钥
- `POST /user/totp/qr`：生成 QR Code

## 安全说明

- Secret Key 不回传明文
- JWT 有效期固定为 30 分钟
- Redis 黑名单 TTL = JWT 剩余有效期
- 注销后 Token 必须命中黑名单

## 开发环境

### 依赖安装

```bash
pip install -r requirements.txt
```

### 启动开发服务器

```bash
uvicorn app.main:app --reload
```

## 生产环境建议

- 使用 HTTPS
- 配置强密码的数据库
- 定期轮换 JWT Secret Key
- 禁用生产环境中的调试模式

## 许可证

MIT License
