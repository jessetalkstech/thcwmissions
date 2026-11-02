from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import IsolatedPasswordContext
from backend.app.config import settings

# Password hashing
pwd_context = IsolatedPasswordContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# JWT helpers
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token
    except JWTError:
        return None
