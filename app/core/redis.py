import redis
from app.core.config import REDIS_URL


class RedisClient:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)
    
    def add_to_blacklist(self, jti, ttl):
        """添加 JWT 到黑名单"""
        if ttl > 0:
            self.client.setex(f"jwt:blacklist:{jti}", ttl, "1")
    
    def is_blacklisted(self, jti):
        """检查 JWT 是否在黑名单中"""
        return self.client.exists(f"jwt:blacklist:{jti}") > 0
    
    def save_refresh_token(self, user_id, token_id, ttl):
        """保存 Refresh Token"""
        self.client.setex(f"refresh:{user_id}:{token_id}", ttl, "valid")
    
    def validate_refresh_token(self, user_id, token_id):
        """验证 Refresh Token"""
        return self.client.exists(f"refresh:{user_id}:{token_id}") > 0
    
    def delete_refresh_token(self, user_id, token_id):
        """删除 Refresh Token"""
        self.client.delete(f"refresh:{user_id}:{token_id}")

redis_client = RedisClient()
