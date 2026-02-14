import pyotp
import base64
import qrcode
from io import BytesIO
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
    
    @staticmethod
    def generate_qr_code(uri):
        """生成 QR Code 图片"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        # 转换为字节流
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

totp_manager = TOTPManager()
