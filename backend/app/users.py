from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import UserCreate, UserRead
from backend.app.auth import hash_password, verify_password, decode_access_token
from backend.app.config import settings
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            raise credentials_exception
        username: str = payload.get("sub")
        user = await get_user_by_username(db, username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_pw = hash_password(user_in.password)
    
    # Determine if this is the first user (make them admin)
    user_count_stmt = select(User)
    user_count_res = await db.execute(user_count_stmt)
    users_list = user_count_res.scalars().all()
    is_first_user = len(users_list) == 0
    
    new_user = User(
        username=user_in.username, 
        hashed_password=hashed_pw, 
        is_admin=is_first_user
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()
