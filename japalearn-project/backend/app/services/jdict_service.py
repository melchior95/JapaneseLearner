"""Japanese dictionary service."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.models.user import User
from app.models.word import JapaneseWord, WordExample
from app.routers.word import KanjiInfo, WordInfo
from app.services.fallback_terms import FallbackTermsService


class JDictService:
    """Japanese dictionary and word information service.

    Implements intelligent word lookup with fallback chains,
    adopted from jidoujisho's multi-level fallback approach.
    """

    def __init__(self):
        self.fallback_service = FallbackTermsService()

    async def get_word_info(
        self, word: str, session: AsyncSession, user: Optional[User] = None
    ) -> WordInfo:
        """
        Get detailed information about a Japanese word.

        Uses 6-level fallback chain to find word definition:
        1. Exact match (original word)
        2. Root form (dictionary form)
        3. Hiragana version
        4. Katakana version
        5. Stripped conjugations
        6. Multiple attempts

        Args:
            word: Japanese word to look up
            session: Database session
            user: Current user (optional)

        Returns:
            Detailed word information
        """
        # Check cache first for exact match
        cache_key = f"word_info:{word}"
        cached = await cache_get(cache_key)
        if cached:
            return WordInfo(**cached)

        # Generate fallback terms using jidoujisho pattern
        fallback_terms = await self.fallback_service.get_fallback_terms(word)

        # Try each fallback term in priority order
        word_obj = None
        found_term = None
        for term in fallback_terms:
            result = await session.execute(select(JapaneseWord).where(JapaneseWord.word == term))
            word_obj = result.scalar_one_or_none()
            if word_obj:
                found_term = term
                break

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
                word=word_obj.word,  # Use actual word from database
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

            # Cache result (both original and found term)
            await cache_set(cache_key, word_info.model_dump(), ttl=86400)
            if found_term and found_term != word:
                found_cache_key = f"word_info:{found_term}"
                await cache_set(found_cache_key, word_info.model_dump(), ttl=86400)

            # Track user progress
            if user:
                await self._track_word_view(session, user, word_obj)

            return word_info

        else:
            # Word not found - even after fallback chain
            # In future, could query external API (JMdict, etc.)
            # For now, return message indicating word not in database
            return WordInfo(
                word=word,
                reading=None,
                romanji=None,
                part_of_speech=None,
                jlpt_level=None,
                definition="[Word not found in database. Tried: " + ", ".join(fallback_terms) + "]",
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
