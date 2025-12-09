"""Translation endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.db import get_session
from app.models.user import User
from app.services.translator import TranslatorService

router = APIRouter()


class TranslateRequest(BaseModel):
    """Translation request."""

    text: str
    source: str = "en"  # Source language code
    target: str = "ja"  # Target language code


class WordToken(BaseModel):
    """Individual word token with metadata."""

    word: str  # Original word (e.g., "注文")
    reading: str | None = None  # Hiragana reading (e.g., "ちゅうもん")
    romanji: str | None = None  # Romanized reading (e.g., "chūmon")
    part_of_speech: str | None = None  # noun, verb, particle, etc.
    base_form: str | None = None  # Dictionary form
    position: int = 0  # Position in sentence


class TranslateResponse(BaseModel):
    """Translation response."""

    original: str
    translated: str
    romanji: str | None = None
    source_lang: str
    target_lang: str
    words: list[WordToken] = []
    translation_service: str = "google"


@router.post("/translate", response_model=TranslateResponse)
async def translate(
    request: TranslateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> TranslateResponse:
    """
    Translate text from source language to target language.

    - Supports English → Japanese primarily
    - Returns tokenized words with linguistic metadata
    - Stores translation in user history if authenticated
    """
    translator = TranslatorService()

    try:
        result = await translator.translate(
            text=request.text,
            source=request.source,
            target=request.target,
            session=session,
            user=current_user,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/history")
async def get_translation_history(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get user's translation history."""
    from sqlalchemy import select

    from app.models.translation import UserTranslation

    result = await session.execute(
        select(UserTranslation)
        .where(UserTranslation.user_id == current_user.id)
        .order_by(UserTranslation.created_at.desc())
        .limit(limit)
    )
    translations = result.scalars().all()

    return [
        {
            "id": t.id,
            "source_text": t.source_text,
            "translated_text": t.translated_text,
            "source_lang": t.source_lang,
            "target_lang": t.target_lang,
            "favorited": t.favorited,
            "created_at": t.created_at.isoformat(),
        }
        for t in translations
    ]


@router.post("/history/{translation_id}/favorite")
async def toggle_favorite(
    translation_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Toggle favorite status on a translation."""
    from sqlalchemy import select

    from app.models.translation import UserTranslation

    result = await session.execute(
        select(UserTranslation).where(
            UserTranslation.id == translation_id,
            UserTranslation.user_id == current_user.id,
        )
    )
    translation = result.scalar_one_or_none()

    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    translation.favorited = not translation.favorited
    await session.commit()

    return {"favorited": translation.favorited}
