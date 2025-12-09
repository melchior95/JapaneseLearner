"""Authentication endpoints."""
from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.core.config import get_settings
from app.core.db import get_session
from app.models.user import User

router = APIRouter()
settings = get_settings()


class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    username: str | None = None


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Access token response."""

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """User response model."""

    id: str
    email: str
    username: str | None
    subscription_tier: str
    total_translations: int
    total_words_learned: int

    class Config:
        from_attributes = True


@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegister, session: AsyncSession = Depends(get_session)
) -> Token:
    """Register a new user."""
    # Check if user exists
    result = await session.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})

    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin, session: AsyncSession = Depends(get_session)
) -> Token:
    """Login user."""
    # Find user
    result = await session.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Get current user profile."""
    return UserOut.model_validate(current_user)
