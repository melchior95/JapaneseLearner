"""Translation history database models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UserTranslation(Base):
    """User translation history."""

    __tablename__ = "user_translations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Translation data
    source_text: Mapped[str] = mapped_column(Text)
    source_lang: Mapped[str] = mapped_column(String(10))  # en, zh, etc.
    translated_text: Mapped[str] = mapped_column(Text)
    target_lang: Mapped[str] = mapped_column(String(10))  # ja

    # Word analysis (array of word IDs that were clicked)
    words_analyzed: Mapped[Optional[dict]] = mapped_column(JSONB)
    # {"words": [{"word": "注文", "word_id": 123, "clicks": 2}, ...]}

    # Metadata
    translation_service: Mapped[Optional[str]] = mapped_column(String(50))
    # google, openai, etc.

    # User actions
    favorited: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<UserTranslation {self.source_text[:30]}...>"
