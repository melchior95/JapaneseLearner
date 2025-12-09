"""Japanese dictionary service."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.models.user import User
from app.models.word import JapaneseWord, WordExample
from app.routers.word import KanjiInfo, WordInfo


class JDictService:
    """Japanese dictionary and word information service."""

    async def get_word_info(
        self, word: str, session: AsyncSession, user: Optional[User] = None
    ) -> WordInfo:
        """
        Get detailed information about a Japanese word.

        Args:
            word: Japanese word to look up
            session: Database session
            user: Current user (optional)

        Returns:
            Detailed word information
        """
        # Check cache
        cache_key = f"word_info:{word}"
        cached = await cache_get(cache_key)
        if cached:
            return WordInfo(**cached)

        # Look up in database
        result = await session.execute(select(JapaneseWord).where(JapaneseWord.word == word))
        word_obj = result.scalar_one_or_none()

        if word_obj:
            # Get examples
            examples_result = await session.execute(
                select(WordExample)
                .where(WordExample.word_id == word_obj.id)
                .limit(3)
            )
            examples = examples_result.scalars().all()

            # Build kanji breakdown
            kanji_breakdown = None
            if word_obj.kanji_breakdown:
                kanji_breakdown = [
                    KanjiInfo(
                        character=k["kanji"],
                        meaning=k["meaning"],
                        reading=k["readings"],
                    )
                    for k in word_obj.kanji_breakdown.get("kanji", [])
                ]

            word_info = WordInfo(
                word=word_obj.word,
                reading=word_obj.reading,
                romanji=word_obj.romanji,
                part_of_speech=word_obj.part_of_speech,
                jlpt_level=word_obj.jlpt_level,
                definition=word_obj.definition_en,
                grammar_notes=word_obj.grammar_notes,
                kanji_breakdown=kanji_breakdown,
                examples=[
                    {
                        "japanese": ex.japanese_text,
                        "english": ex.english_translation,
                        "romanji": ex.romanji,
                    }
                    for ex in examples
                ],
            )

            # Cache result
            await cache_set(cache_key, word_info.model_dump(), ttl=86400)

            # Track user progress
            if user:
                await self._track_word_view(session, user, word_obj)

            return word_info

        else:
            # Word not in database - return basic info
            # In production, query external API (JMdict, etc.)
            return WordInfo(
                word=word,
                reading=None,
                romanji=None,
                part_of_speech=None,
                jlpt_level=None,
                definition="[Word not found in dictionary]",
            )

    async def _track_word_view(
        self, session: AsyncSession, user: User, word: JapaneseWord
    ) -> None:
        """Track that user viewed this word."""
        from datetime import datetime, timezone

        from app.models.word import UserWordProgress

        # Find or create progress record
        result = await session.execute(
            select(UserWordProgress).where(
                UserWordProgress.user_id == user.id,
                UserWordProgress.word_id == word.id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.times_seen += 1
            progress.last_reviewed = datetime.now(timezone.utc)
        else:
            progress = UserWordProgress(
                user_id=user.id, word_id=word.id, times_seen=1
            )
            session.add(progress)

        await session.commit()
