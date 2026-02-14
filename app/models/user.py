from app.core.database import db
from app.core.totp import totp_manager


class UserManager:
    @staticmethod
    def create_user(username, role):
        """创建用户并生成 TOTP 密钥"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                # 创建用户
                cur.execute(
                    "INSERT INTO users (username, role) VALUES (%s, %s) RETURNING id",
                    (username, role)
                )
                user_id = cur.fetchone()[0]
                
                # 生成 TOTP 密钥
                secret = totp_manager.generate_secret()
                
                # 保存 TOTP 密钥
                cur.execute(
                    "INSERT INTO user_totp_secrets (user_id, secret) VALUES (%s, %s)",
                    (user_id, secret)
                )
                
                conn.commit()
                
                # 生成 otpauth URI
                uri = totp_manager.generate_otpauth_uri(username, secret)
                
                return user_id, username, role, uri
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户信息"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, role, is_active FROM users WHERE username = %s",
                    (username,)
                )
                user = cur.fetchone()
                if not user:
                    return None
                return {
                    "id": user[0],
                    "username": user[1],
                    "role": user[2],
                    "is_active": user[3]
                }
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据 ID 获取用户信息"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, role, is_active FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cur.fetchone()
                if not user:
                    return None
                return {
                    "id": user[0],
                    "username": user[1],
                    "role": user[2],
                    "is_active": user[3]
                }
    
    @staticmethod
    def get_user_totp_secret(user_id):
        """获取用户当前的 TOTP 密钥"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT secret FROM user_totp_secrets WHERE user_id = %s AND is_current = TRUE",
                    (user_id,)
                )
                secret = cur.fetchone()
                return secret[0] if secret else None
    
    @staticmethod
    def rotate_totp_secret(user_id, username):
        """轮换用户的 TOTP 密钥"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                # 标记旧密钥为非当前
                cur.execute(
                    "UPDATE user_totp_secrets SET is_current = FALSE WHERE user_id = %s AND is_current = TRUE",
                    (user_id,)
                )
                
                # 生成新密钥
                secret = totp_manager.generate_secret()
                
                # 保存新密钥
                cur.execute(
                    "INSERT INTO user_totp_secrets (user_id, secret) VALUES (%s, %s)",
                    (user_id, secret)
                )
                
                conn.commit()
                
                # 生成新的 otpauth URI
                uri = totp_manager.generate_otpauth_uri(username, secret)
                
                return uri
    
    @staticmethod
    def disable_user(user_id):
        """禁用用户"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET is_active = FALSE WHERE id = %s",
                    (user_id,)
                )
                conn.commit()
                return cur.rowcount > 0
    
    @staticmethod
    def init_super_admin():
        """初始化超级管理员"""
        with db.connect() as conn:
            with conn.cursor() as cur:
                # 检查是否已存在 admin 用户
                cur.execute(
                    "SELECT id FROM users WHERE username = 'admin'"
                )
                if cur.fetchone():
                    return False
                
                # 创建超级管理员
                user_id, username, role, uri = UserManager.create_user('admin', 'super_admin')
                return user_id, username, role, uri

user_manager = UserManager()
