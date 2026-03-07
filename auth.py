# auth.py
from datetime import datetime, timedelta
from typing import Optional
from database import get_db
from jose import JWTError, jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import crud
import models
from database import get_db  # your existing DB session dependency

# =============================
# CONFIGURATION
# =============================
SECRET_KEY = "your_secret_key_here"  # replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  # path to your login endpoint

# =============================
# PASSWORD HASHING (ARGON2)
# =============================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except argon2_exceptions.VerifyMismatchError:
        return False

def get_password_hash(password: str) -> str:
    return ph.hash(password)

# =============================
# JWT TOKEN FUNCTIONS
# =============================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str|None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

# auth.py
def verify_access_token(token: str):
    # your implementation
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # return the payload for further use (e.g., get user info)  
    except JWTError:
        return None  # or raise an exception if you prefer
    

# =============================
# OPTIONAL: Admin Check
# =============================
def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user or not bool(current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user