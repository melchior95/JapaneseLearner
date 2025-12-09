"""Word information and explanation endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.db import get_session
from app.models.user import User
from app.services.grammar_service import GrammarService
from app.services.jdict_service import JDictService

router = APIRouter()


class KanjiInfo(BaseModel):
    """Kanji character information."""

    character: str
    meaning: str
    reading: list[str]


class WordInfo(BaseModel):
    """Detailed word information."""

    word: str
    reading: str | None
    romanji: str | None
    part_of_speech: str | None
    jlpt_level: int | None
    definition: str | None
    grammar_notes: dict | None = None
    kanji_breakdown: list[KanjiInfo] | None = None
    examples: list[dict] | None = None


class ExplainRequest(BaseModel):
    """Request for sentence explanation."""

    sentence: str
    detail_level: str = "comprehensive"  # basic, intermediate, comprehensive


class GrammarBreakdown(BaseModel):
    """Grammar breakdown for a sentence part."""

    part: str
    role: str
    explanation: str


class ExplainResponse(BaseModel):
    """Detailed sentence explanation."""

    sentence: str
    explanation: str
    grammar_breakdown: list[GrammarBreakdown]
    cultural_context: str | None = None
    alternative_phrasings: list[str] | None = None


@router.get("/{word}/info", response_model=WordInfo)
async def get_word_info(
    word: str,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> WordInfo:
    """
    Get detailed information about a Japanese word.

    - Returns dictionary definition, readings, examples
    - Kanji breakdown with meanings
    - JLPT level and grammar notes
    """
    jdict_service = JDictService()

    try:
        info = await jdict_service.get_word_info(
            word=word, session=session, user=current_user
        )
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get word info: {str(e)}")


@router.post("/explain", response_model=ExplainResponse)
async def explain_sentence(
    request: ExplainRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> ExplainResponse:
    """
    Get AI-powered comprehensive explanation of a Japanese sentence.

    - Grammar breakdown with detailed explanations
    - Cultural context
    - Alternative ways to say the same thing
    - Usage notes and common mistakes
    """
    grammar_service = GrammarService()

    try:
        explanation = await grammar_service.explain_sentence(
            sentence=request.sentence,
            detail_level=request.detail_level,
            user=current_user,
        )
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to explain sentence: {str(e)}"
        )


@router.get("/{word}/examples")
async def get_word_examples(
    word: str,
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
):
    """Get example sentences for a word."""
    from sqlalchemy import select

    from app.models.word import JapaneseWord, WordExample

    # Find word
    result = await session.execute(select(JapaneseWord).where(JapaneseWord.word == word))
    word_obj = result.scalar_one_or_none()

    if not word_obj:
        raise HTTPException(status_code=404, detail="Word not found")

    # Get examples
    result = await session.execute(
        select(WordExample)
        .where(WordExample.word_id == word_obj.id)
        .limit(limit)
    )
    examples = result.scalars().all()

    return [
        {
            "japanese": ex.japanese_text,
            "english": ex.english_translation,
            "romanji": ex.romanji,
            "difficulty": ex.difficulty_level,
            "context": ex.context,
        }
        for ex in examples
    ]
