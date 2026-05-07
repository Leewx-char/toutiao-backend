from passlib.context import CryptContext

# 创建密码上下文
pwd_content = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码加密
def get_hash_password(password: str):
    return pwd_content.hash(password)

# 密码验证
def verify_password(plain_password, hashed_password):
    return pwd_content.verify(plain_password, hashed_password)