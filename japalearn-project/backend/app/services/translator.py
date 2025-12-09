"""Translation service using Google Translate."""
from __future__ import annotations

from typing import Optional

from googletrans import Translator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_exists, cache_get, cache_set
from app.models.user import User
from app.routers.translate import TranslateResponse, WordToken
from app.services.tokenizer import TokenizerService


class TranslatorService:
    """Handle translation between languages."""

    def __init__(self):
        self.translator = Translator()
        self.tokenizer = TokenizerService()

    async def translate(
        self,
        text: str,
        source: str,
        target: str,
        session: AsyncSession,
        user: Optional[User] = None,
    ) -> TranslateResponse:
        """
        Translate text and tokenize if target is Japanese.

        Args:
            text: Text to translate
            source: Source language code
            target: Target language code
            session: Database session
            user: Current user (optional)

        Returns:
            TranslateResponse with translation and word tokens
        """
        # Check cache
        cache_key = f"translate:{source}:{target}:{text}"
        cached = await cache_get(cache_key)
        if cached:
            return TranslateResponse(**cached)

        # Translate
        try:
            result = self.translator.translate(text, src=source, dest=target)
            translated_text = result.text
        except Exception as e:
            # Fallback: if googletrans fails, use simple echo for now
            # In production, use Google Cloud Translate API
            translated_text = f"[Translation Error: {str(e)}]"

        # Tokenize if target is Japanese
        words = []
        romanji = None
        if target == "ja":
            try:
                tokens = await self.tokenizer.tokenize(translated_text)
                words = [
                    WordToken(
                        word=t["surface"],
                        reading=t.get("reading"),
                        romanji=t.get("romanji"),
                        part_of_speech=t.get("pos"),
                        base_form=t.get("base_form"),
                        position=i,
                    )
                    for i, t in enumerate(tokens)
                ]
                # Generate romanji for full sentence
                romanji = " ".join([w.romanji or w.word for w in words if w.romanji])
            except Exception as e:
                print(f"Tokenization error: {e}")

        response = TranslateResponse(
            original=text,
            translated=translated_text,
            romanji=romanji,
            source_lang=source,
            target_lang=target,
            words=words,
            translation_service="googletrans",
        )

        # Cache result
        await cache_set(cache_key, response.model_dump(), ttl=86400)  # 24 hours

        # Store in user history
        if user:
            from app.models.translation import UserTranslation

            translation_record = UserTranslation(
                user_id=user.id,
                source_text=text,
                source_lang=source,
                translated_text=translated_text,
                target_lang=target,
                translation_service="googletrans",
            )
            session.add(translation_record)
            user.total_translations += 1
            await session.commit()

        return response
