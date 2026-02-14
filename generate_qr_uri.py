from app.core.totp import totp_manager

# Admin 用户的信息
username = "admin"
secret = "KBEUMSCCKFBE2QKVKBDDMTCXJNMUQUKYKJJFCQKIGZHE2RSVKE3A===="

# 生成 otpauth URI
uri = totp_manager.generate_otpauth_uri(username, secret)
print("OTP Auth URI:")
print(uri)
print("\nYou can use this URI to generate a QR code or directly add it to your Authenticator App.")