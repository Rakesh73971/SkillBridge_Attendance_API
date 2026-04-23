from fastapi.security import OAuth2PasswordBearer
from . import schemas, models
from .database import get_db
from sqlalchemy.orm import Session
from .config import settings
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta, timezone
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
STANDARD_TOKEN_TYPE = "access"
MONITORING_TOKEN_TYPE = "monitoring"

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def decode_token(token: str, credential_exception):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credential_exception

def create_access_token(data: dict):
    
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'iat': issued_at, 'exp': expire, 'token_type': STANDARD_TOKEN_TYPE})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


def verify_access_token(token: str, credential_exception):

    payload = decode_token(token, credential_exception)
    user_id: int = payload.get("user_id")
    role: str = payload.get("role")

    if user_id is None:
        raise credential_exception
    return schemas.TokenData(user_id=user_id, role=role)
    

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    token_data = verify_access_token(token, credential_exception)

    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise credential_exception
    if token_data.role != user.role.value:
        raise credential_exception
    return user


class RoleChecker:
    
    def __init__(self, allowed_roles: List[models.RoleEnum]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: models.User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user


def create_scoped_monitoring_token(data: dict):

    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(minutes=60)
    to_encode.update({'iat': issued_at, 'exp': expire, 'token_type': MONITORING_TOKEN_TYPE})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


def get_monitoring_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid or expired monitoring token',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    
    payload = decode_token(token, credential_exception)
    token_data = schemas.TokenData(user_id=payload.get("user_id"), role=payload.get("role"))

    if token_data.user_id is None:
        raise credential_exception
    
    if token_data.role != models.RoleEnum.MONITORING_OFFICER.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token is not issued for monitoring officer role'
        )
    if payload.get("token_type") != MONITORING_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Scoped monitoring token required'
        )
    
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None or user.role != models.RoleEnum.MONITORING_OFFICER:
        raise credential_exception
    return user
