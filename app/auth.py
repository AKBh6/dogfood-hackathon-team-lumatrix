import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, RoleEnum

SECRET_KEY = os.getenv("SECRET_KEY", "dogfood-local-demo-secret-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS = 24

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except (ValueError, TypeError):
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=TOKEN_EXPIRE_HOURS))
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("missing subject")
        user = db.query(User).filter(User.id == int(user_id)).first()
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired authentication.")
    if not user:
        raise HTTPException(status_code=401, detail="User account no longer exists.")
    return user

def require_roles(*roles: RoleEnum):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to access this resource.")
        return user
    return dependency

def redirect_or_raise(request: Request, user: User | None, *roles: RoleEnum):
    if user is None:
        raise HTTPException(status_code=303, detail="Login required.", headers={"Location": "/login"})
    if roles and user.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    return user
