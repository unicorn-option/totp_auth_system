# 基于 TOTP 的账号管理与登录 Demo 开发文档

## 1. 项目目标与范围

### 目标
实现一个 **基于 TOTP 动态密码的账号管理与登录系统 Demo**，包含：

- 后台：账号生命周期管理
- 前台：TOTP 登录 + Token 管理
- 不依赖短信 / 邮件
- Authenticator App 扫码即可登录

### 非目标（Demo 中不做）
- 风控 / IP 限制
- 硬件 Key（FIDO2）
- OAuth / SSO
- 多租户复杂权限

---

## 2. 技术栈说明

- Python 3.12
- FastAPI
- Jinja2（服务端模板渲染）
- PostgreSQL
- Redis
- TOTP（RFC 6238）
- JWT（Access Token + Refresh Token）
- QR Code（otpauth URI）

---

## 3. 系统总体架构

```
┌──────────────────┐
│ Browser          │
│  Jinja2 页面     │
└─────────▲────────┘
          │ HTML
          │
┌─────────┴────────┐
│ FastAPI          │
│  - API           │
│  - Jinja2 Render │
└─────────▲────────┘
          │
 ┌────────┴─────────┐
 │ PostgreSQL       │
 │  - users         │
 │  - totp_secrets  │
 └──────────────────┘
          │
 ┌────────┴─────────┐
 │ Redis            │
 │  - tokens        │
 │  - blacklist     │
 └──────────────────┘
```

---

## 4. 核心安全模型

### 认证因子

| 因子 | 内容 |
|----|----|
| 知识 | 账号名 |
| 持有 | TOTP 动态密码 |

> Demo 中不使用传统密码，只使用：
> **账号 + 动态密码**

---

## 5. 数据库设计（PostgreSQL）

### 5.1 用户表 users

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    role VARCHAR(16) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

---

### 5.2 TOTP 密钥表 user_totp_secrets

```sql
CREATE TABLE user_totp_secrets (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    secret VARCHAR(64) NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

说明：
- 一个用户可拥有多个历史密钥
- 仅 `is_current = true` 的密钥用于校验
- 密钥轮换通过新增记录完成

---

## 6. Redis 设计

### 6.1 JWT 黑名单

```
key: jwt:blacklist:{jti}
value: 1
ttl: 剩余有效期
```

### 6.2 Refresh Token

```
key: refresh:{user_id}:{token_id}
value: valid
ttl: 7d
```

---

## 7. 后台：账号管理

### 7.1 超级管理员初始化

- 系统首次启动自动生成
- 用户名：admin
- 角色：super_admin
- 自动生成 TOTP 密钥
- 首次启动时输出 QR Code

---

### 7.2 创建账号

```
POST /admin/users
```

流程：
1. 校验超级管理员权限
2. 创建用户
3. 生成 TOTP Secret
4. 生成 otpauth URI
5. 返回 QR Code

---

### 7.3 关闭账号

```
POST /admin/users/{id}/disable
```

行为：
- 标记用户为不可用
- 注销该用户全部 Token

---

## 8. 前台：登录与认证

### 8.1 登录接口

```
POST /auth/login
```

参数示例：
```json
{
  "username": "demo",
  "totp_code": "123456"
}
```

流程：
1. 校验账号状态
2. 校验 TOTP（允许 ±1 时间窗口）
3. 生成 Access Token
4. 生成 Refresh Token

---

### 8.2 Token 结构

#### Access Token

- 有效期：**30 分钟**

```json
{
  "sub": "user_id",
  "role": "user",
  "jti": "uuid",
  "iat": 1700000000,
  "exp": 1700001800
}
```

说明：
- `iat`：签发时间
- `exp`：过期时间（iat + 30min）

#### Refresh Token

- UUID
- 存储在 Redis
- 用于刷新 Access Token

---

### 8.3 注销登录

```
POST /auth/logout
```

流程：
1. 从 JWT 中解析 `jti`、`iat`、`exp`
2. 计算 Token 已使用时间
3. 将 `jti` 写入 Redis 黑名单
4. **黑名单 TTL = 30 分钟 - 已使用时间**
5. 删除 Refresh Token

TTL 计算公式：

```
ttl = exp - current_time
```

当 `ttl <= 0` 时无需写入黑名单。

---

## 9. 用户中心

### 9.1 密钥轮换

```
POST /user/totp/rotate
```

流程：
1. 校验 Access Token
2. 生成新 TOTP Secret
3. 旧密钥失效
4. 返回新 QR Code

---

## 10. TOTP 实现说明

- 使用 Base32 Secret
- 时间步长：30 秒
- 位数：6 位
- otpauth URI 示例：

```
otpauth://totp/DemoApp:user?secret=BASE32&issuer=DemoApp
```

---

## 11. 安全建议（Demo 级）

- Secret 不回传明文
- JWT 有效期固定为 30 分钟
- Redis 黑名单 TTL = JWT 剩余有效期
- 注销后 Token 必须命中黑名单
- 禁止生产环境打印 QR Code

---

## 12. Jinja2 页面渲染说明

### 页面渲染模式

- 使用 **Jinja2** 作为服务端模板引擎
- 页面由 FastAPI 返回 HTML
- 动态数据通过模板变量注入

### 页面示例

| 页面 | 说明 |
|----|----|
| /login | 登录页（账号 + TOTP） |
| /admin | 管理后台（用户列表 + 创建用户 + 禁用用户） |
| /user | 用户中心（TOTP 管理） |

### 登录页面逻辑（示例）

1. GET /login
   - 返回登录页面
2. POST /auth/login
   - 校验 TOTP
   - 返回 JWT
3. 前端通过 Cookie / Header 保存 Token

### 管理后台功能

1. **用户列表**：
   - 显示 ID、Username、Role、Status（激活/未激活）
   - 按 ID 排序

2. **创建用户**：
   - 表单提交
   - 返回 QR Code 供扫描

3. **禁用用户**：
   - 点击删除按钮确认后禁用

### 用户中心功能

1. **Rotate TOTP Secret**：
   - 重新生成 Secret Key
   - 生成新的 QR Code

2. **Generate QR Code**：
   - 使用当前 Secret Key 生成 QR Code
   - 不更新 Secret Key

---

## 13. 后续扩展方向

- 登录失败次数限制
- 管理员强制密钥轮换
- WebAuthn / Passkey
- 多设备管理

---

## 13. Docker 化部署方案

本 Demo 支持 **代码 + 数据库 + 缓存全部运行在容器中**，适合本地开发与联调。

---

### 13.1 Dockerfile（FastAPI 应用）

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 系统依赖
RUN apt-get update \
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

说明：
- 使用 Python 3.12 官方 slim 镜像
- 通过 `uvicorn` 启动 FastAPI
- 适用于 Jinja2 + API 混合模式

---

### 13.2 requirements.txt 示例

```text
fastapi
uvicorn[standard]
python-jose[cryptography]
passlib
pyotp
qrcode[pil]
psycopg[binary]
redis
jinja2
```

---

### 13.3 docker-compose.yml

```yaml
version: "3.9"

services:
  web:
    build: .
    container_name: totp_demo_web
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://demo:demo@db:5432/demo_db
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: dev-secret-key
    volumes:
      - .:/app
    restart: unless-stopped

  db:
    image: postgres:16
    container_name: totp_demo_db
    environment:
      POSTGRES_USER: demo
      POSTGRES_PASSWORD: demo
      POSTGRES_DB: demo_db
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7
    container_name: totp_demo_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  pg_data:
  redis_data:
```

---

### 13.4 容器启动顺序

```
docker compose up -d --build
```

访问地址：
- Web / API：http://localhost:8000
- PostgreSQL：localhost:5432
- Redis：localhost:6379

---

### 13.5 FastAPI 配置读取建议

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
```

---

## 14. 总结

至此，本 Demo 已具备：

- TOTP 无密码登录
- JWT + Redis 黑名单
- Jinja2 服务端渲染
- PostgreSQL + Redis
- **完整 Docker / Docker Compose 本地运行环境**

该结构非常适合作为：
- 内部系统模板
- 管理后台安全基线
- FastAPI 认证示例项目

