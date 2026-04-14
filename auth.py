import time
from typing import Dict

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import ACCESS_TOKEN_EXPIRE_SECONDS, ALGORITHM, SECRET_KEY

security = HTTPBearer()

USER_PASSWORDS: Dict[str, bytes] = {
    "alice": bcrypt.hashpw("alice123".encode(), bcrypt.gensalt()),
    "bob": bcrypt.hashpw("bobPassword".encode(), bcrypt.gensalt()),
}


def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password)


def authenticate_user(username: str, password: str) -> bool:
    hashed_password = USER_PASSWORDS.get(username)
    if not hashed_password:
        return False
    return verify_password(password, hashed_password)


def create_token(username: str) -> str:
    payload = {"sub": username, "exp": time.time() + ACCESS_TOKEN_EXPIRE_SECONDS}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
