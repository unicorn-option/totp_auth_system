from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models.user import user_manager
from app.core.totp import totp_manager
from app.core.jwt import jwt_manager
from app.core.redis import redis_client

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/auth/login")
async def login(username: str = Form(...), totp_code: str = Form(...)):
    """登录接口"""
    # 1. 校验账号状态
    user = user_manager.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or code")
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="User is disabled")
    
    # 2. 校验 TOTP
    secret = user_manager.get_user_totp_secret(user["id"])
    if not secret:
        raise HTTPException(status_code=500, detail="TOTP secret not found")
    if not totp_manager.verify_code(secret, totp_code):
        raise HTTPException(status_code=401, detail="Invalid username or code")
    
    # 3. 生成 Access Token
    access_token, _, _ = jwt_manager.create_access_token(user["id"], user["role"])
    
    # 4. 生成 Refresh Token
    refresh_token = jwt_manager.create_refresh_token(user["id"])
    
    # 5. 返回 Token
    response = RedirectResponse(url="/admin" if user["role"] == "super_admin" else "/user", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return response


@router.post("/auth/logout")
async def logout(request: Request):
    """注销登录"""
    # 从请求中获取 Access Token
    access_token = request.cookies.get("access_token")
    if access_token:
        # 将 Token 加入黑名单
        jwt_manager.blacklist_token(access_token)
    
    # 清除 Cookie
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response


@router.post("/user/totp/rotate")
async def rotate_totp(request: Request):
    """轮换 TOTP 密钥"""
    # 验证 Access Token
    access_token = request.cookies.get("access_token")
    if not access_token or not jwt_manager.validate_token(access_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 解析用户信息
    payload = jwt_manager.decode_token(access_token)
    user_id = int(payload["sub"])
    
    # 获取用户信息
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 轮换密钥
    uri = user_manager.rotate_totp_secret(user_id, user["username"])
    
    # 生成 QR Code
    qr_code = totp_manager.generate_qr_code(uri)
    
    # 返回 QR Code 图片
    from fastapi.responses import StreamingResponse
    return StreamingResponse(qr_code, media_type="image/png")

@router.post("/user/totp/qr")
async def generate_qr(request: Request):
    """生成当前 Secret Key 的 QR Code"""
    # 验证 Access Token
    access_token = request.cookies.get("access_token")
    if not access_token or not jwt_manager.validate_token(access_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 解析用户信息
    payload = jwt_manager.decode_token(access_token)
    user_id = int(payload["sub"])
    
    # 获取用户信息
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 获取当前 Secret Key
    secret = user_manager.get_user_totp_secret(user_id)
    if not secret:
        raise HTTPException(status_code=500, detail="TOTP secret not found")
    
    # 生成 otpauth URI
    uri = totp_manager.generate_otpauth_uri(user["username"], secret)
    
    # 生成 QR Code
    qr_code = totp_manager.generate_qr_code(uri)
    
    # 返回 QR Code 图片
    from fastapi.responses import StreamingResponse
    return StreamingResponse(qr_code, media_type="image/png")
