import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.redis import redis_client


class JWTManager:
    @staticmethod
    def create_access_token(user_id, role):
        """创建 Access Token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "role": role,
            "jti": str(uuid.uuid4()),
            "iat": datetime.utcnow(),
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
        return encoded_jwt, to_encode["jti"], expire
    
    @staticmethod
    def create_refresh_token(user_id):
        """创建 Refresh Token"""
        token_id = str(uuid.uuid4())
        ttl = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        redis_client.save_refresh_token(user_id, token_id, ttl)
        return token_id
    
    @staticmethod
    def decode_token(token):
        """解码 JWT 令牌"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def validate_token(token):
        """验证 JWT 令牌"""
        payload = JWTManager.decode_token(token)
        if not payload:
            return False
        
        # 检查是否过期
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            return False
        
        # 检查是否在黑名单中（添加异常处理）
        jti = payload.get("jti")
        if jti:
            try:
                if redis_client.is_blacklisted(jti):
                    return False
            except Exception:
                # 如果Redis连接失败，忽略黑名单检查，继续验证
                pass
        
        return True
    
    @staticmethod
    def blacklist_token(token):
        """将 JWT 令牌加入黑名单"""
        payload = JWTManager.decode_token(token)
        if not payload:
            return False
        
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return False
        
        # 计算剩余有效期
        current_time = datetime.utcnow().timestamp()
        ttl = int(exp - current_time)
        
        # 添加到黑名单
        redis_client.add_to_blacklist(jti, ttl)
        return True

jwt_manager = JWTManager()
