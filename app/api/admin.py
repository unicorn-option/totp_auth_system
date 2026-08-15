from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.models.user import user_manager
from app.core.jwt import jwt_manager
from app.core.totp import totp_manager
from app.core.database import db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def verify_admin(request: Request):
    """验证管理员权限"""
    access_token = request.cookies.get("access_token")
    if not access_token or not jwt_manager.validate_token(access_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    payload = jwt_manager.decode_token(access_token)
    if payload["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return payload


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理后台页面"""
    verify_admin(request)
    
    # 获取用户列表
    users = get_users()
    
    return templates.TemplateResponse("admin-vue.html", {"request": request, "users": users})

def get_users():
    """获取用户列表"""
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, role, is_active FROM users ORDER BY id"
            )
            users = []
            for row in cur.fetchall():
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "role": row[2],
                    "is_active": "激活" if row[3] else "未激活",
                    "is_active_bool": row[3]
                })
            return users


@router.post("/admin/users")
async def create_user(request: Request, username: str = Form(...)):
    """创建账号"""
    # 1. 校验超级管理员权限
    verify_admin(request)
    
    # 2. 创建用户
    user_id, username, role, uri = user_manager.create_user(username, "user")
    
    # 3. 返回 QR Code URI
    return {"uri": uri, "username": username}


@router.post("/admin/users/{id}/disable")
async def disable_user_by_id(request: Request, id: int):
    """关闭账号"""
    # 1. 校验超级管理员权限
    verify_admin(request)
    
    # 2. 禁用用户
    success = user_manager.disable_user(id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User disabled successfully"}

@router.get("/api/users")
async def get_users_api(request: Request, page: int = 1, limit: int = 10):
    """获取用户列表 API"""
    # 校验超级管理员权限
    verify_admin(request)
    
    # 获取用户列表
    users = get_users()
    
    # 分页处理
    total = len(users)
    start = (page - 1) * limit
    end = start + limit
    paginated_users = users[start:end]
    
    return {
        "users": paginated_users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.post("/admin/users/disable")
async def disable_user(request: Request, user_id: int = Form(...)):
    """关闭账号（表单提交）"""
    # 1. 校验超级管理员权限
    verify_admin(request)
    
    # 2. 禁用用户
    success = user_manager.disable_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User disabled successfully"}
