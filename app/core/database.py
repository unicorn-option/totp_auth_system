import psycopg
from app.core.config import DATABASE_URL


class Database:
    def __init__(self):
        self.conn = None
    
    def connect(self):
        self.conn = psycopg.connect(DATABASE_URL)
        return self.conn
    
    def init_tables(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                # 创建用户表
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    role VARCHAR(16) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT now()
                )
                """)
                
                # 创建 TOTP 密钥表
                cur.execute("""
                CREATE TABLE IF NOT EXISTS user_totp_secrets (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id),
                    secret VARCHAR(64) NOT NULL,
                    is_current BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT now()
                )
                """)
                
                conn.commit()

db = Database()
