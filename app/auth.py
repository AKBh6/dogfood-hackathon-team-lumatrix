import os
from datetime import datetime,timedelta,timezone
from typing import Optional
import bcrypt,jwt
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User,RoleEnum
SECRET_KEY=os.getenv("SECRET_KEY","dogfood-local-demo-secret-change-me")
ALGORITHM=os.getenv("ALGORITHM","HS256")
def hash_password(password): return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
def verify_password(plain_password,hashed_password):
    try:return bcrypt.checkpw(plain_password.encode(),hashed_password.encode())
    except (ValueError,TypeError):return False
def create_access_token(data,expires_delta:Optional[timedelta]=None):
    payload=data.copy(); payload["exp"]=datetime.now(timezone.utc)+(expires_delta or timedelta(hours=24)); return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
def get_current_user(request:Request,db:Session=Depends(get_db)):
    token=request.cookies.get("access_token")
    if not token: raise HTTPException(401,"Authentication required.")
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM]); user_id=payload.get("sub")
        if user_id is None: raise ValueError
        user=db.query(User).filter(User.id==int(user_id)).first()
    except (jwt.PyJWTError,ValueError,TypeError): raise HTTPException(401,"Invalid or expired authentication.")
    if not user: raise HTTPException(401,"User account no longer exists.")
    return user
def require_roles(*roles):
    def dependency(user:User=Depends(get_current_user)):
        if user.role not in roles: raise HTTPException(403,"You do not have permission to access this resource.")
        return user
    return dependency
