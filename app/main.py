from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.database import db
from app.models.user import user_manager
from app.core.totp import totp_manager
from app.api import auth, admin, user

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    # 1. 初始化数据库表
    db.init_tables()
    
    # 2. 初始化超级管理员
    result = user_manager.init_super_admin()
    if result:
        user_id, username, role, uri = result
        # 生成 QR Code 并打印
        qr_code = totp_manager.generate_qr_code(uri)
        print("\n=== Super Admin Initialized ===")
        print(f"Username: {username}")
        print(f"Role: {role}")
        print("Please scan the QR code below with your Authenticator App:")
        print("================================")
    
    yield
    
    # 关闭时执行的清理逻辑
    print("\n=== Application Shutdown ===")
    # 这里可以添加数据库连接关闭、Redis 连接关闭等清理操作
    print("Cleanup completed successfully")

# 创建 FastAPI 应用
app = FastAPI(
    title="TOTP Auth System",
    description="基于 TOTP 动态密码的账号管理与登录系统 Demo",
    version="1.0.0",
    lifespan=lifespan
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 注册路由
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {"message": "TOTP Auth System API", "docs": "/docs"}
