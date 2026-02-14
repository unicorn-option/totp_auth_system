from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.jwt import jwt_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def verify_user(request: Request):
    """验证用户权限"""
    access_token = request.cookies.get("access_token")
    if not access_token or not jwt_manager.validate_token(access_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return jwt_manager.decode_token(access_token)


@router.get("/user", response_class=HTMLResponse)
async def user_page(request: Request):
    """用户中心页面"""
    verify_user(request)
    return templates.TemplateResponse("user.html", {"request": request})
