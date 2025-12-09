"""User database models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))

    # Profile
    native_language: Mapped[Optional[str]] = mapped_column(String(10), default="en")
    target_language: Mapped[Optional[str]] = mapped_column(String(10), default="ja")

    # Subscription
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free")
    # free, pro, premium

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Stats
    total_translations: Mapped[int] = mapped_column(default=0)
    total_words_learned: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
