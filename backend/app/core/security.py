# app/core/security.py

from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt_sha256
import bcrypt as pybcrypt
from app.core.config import settings
from fastapi import Header, HTTPException
import hashlib

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str) -> str:
    # Pre-hash to 32-byte digest, then bcrypt using low-level bcrypt module
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return pybcrypt.hashpw(digest, pybcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    # bcrypt_sha256 hashes (if any) are handled by passlib's verifier
    try:
        if hashed.startswith("$bcrypt-sha256$"):
            return bcrypt_sha256.verify(password, hashed)
    except Exception:
        pass

    # Preferred path: compare bcrypt of 32-byte digest via low-level bcrypt
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    try:
        return pybcrypt.checkpw(digest, hashed.encode())
    except Exception:
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user(token: str = Header(...)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
