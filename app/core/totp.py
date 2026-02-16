import pyotp
import base64
from app.core.config import TOTP_ISSUER, TOTP_DIGITS, TOTP_INTERVAL


class TOTPManager:
    @staticmethod
    def generate_secret():
        """生成 TOTP 密钥"""
        return base64.b32encode(pyotp.random_base32().encode()).decode()
    
    @staticmethod
    def get_totp(secret):
        """获取 TOTP 对象"""
        return pyotp.TOTP(
            secret,
            digits=TOTP_DIGITS,
            interval=TOTP_INTERVAL,
            issuer=TOTP_ISSUER
        )
    
    @staticmethod
    def verify_code(secret, code):
        """验证 TOTP 验证码（允许 ±1 时间窗口）"""
        totp = TOTPManager.get_totp(secret)
        return totp.verify(code, valid_window=1)
    
    @staticmethod
    def generate_otpauth_uri(username, secret):
        """生成 otpauth URI"""
        return f"otpauth://totp/{TOTP_ISSUER}:{username}?secret={secret}&issuer={TOTP_ISSUER}"

totp_manager = TOTPManager()
