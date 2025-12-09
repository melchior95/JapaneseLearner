"""Japanese word database models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class JapaneseWord(Base):
    """Japanese vocabulary database."""

    __tablename__ = "japanese_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Word forms
    word: Mapped[str] = mapped_column(Text, index=True)  # 注文
    reading: Mapped[Optional[str]] = mapped_column(Text)  # ちゅうもん
    romanji: Mapped[Optional[str]] = mapped_column(Text)  # chūmon

    # Linguistic info
    part_of_speech: Mapped[Optional[str]] = mapped_column(String(50))
    jlpt_level: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 (N1-N5)
    frequency_rank: Mapped[Optional[int]] = mapped_column(Integer)

    # Definitions
    definition_en: Mapped[Optional[str]] = mapped_column(Text)
    definition_zh: Mapped[Optional[str]] = mapped_column(Text)

    # Detailed information (JSON)
    grammar_notes: Mapped[Optional[dict]] = mapped_column(JSONB)
    kanji_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB)
    # {
    #   "kanji": ["注", "文"],
    #   "meanings": ["pour", "sentence"],
    #   "readings": ["チュウ", "モン"]
    # }

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<JapaneseWord {self.word}>"


class WordExample(Base):
    """Example sentences for words."""

    __tablename__ = "word_examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("japanese_words.id", ondelete="CASCADE")
    )

    japanese_text: Mapped[str] = mapped_column(Text)
    english_translation: Mapped[Optional[str]] = mapped_column(Text)
    romanji: Mapped[Optional[str]] = mapped_column(Text)

    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    context: Mapped[Optional[str]] = mapped_column(String(100))
    # casual, formal, business, etc.

    def __repr__(self) -> str:
        return f"<WordExample {self.japanese_text[:20]}...>"


class UserWordProgress(Base):
    """Track user's learning progress for each word."""

    __tablename__ = "user_word_progress"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("japanese_words.id", ondelete="CASCADE")
    )

    # Learning stats
    times_seen: Mapped[int] = mapped_column(Integer, default=1)
    times_clicked: Mapped[int] = mapped_column(Integer, default=0)
    mastery_level: Mapped[int] = mapped_column(Integer, default=0)  # 0-5

    # Spaced repetition
    last_reviewed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<UserWordProgress user={self.user_id} word={self.word_id}>"
