"""Voice recognition and TTS endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.db import get_session
from app.models.user import User
from app.services.openai_service import OpenAIService

router = APIRouter()


class RecognizeResponse(BaseModel):
    """Speech recognition response."""

    text: str
    language: str
    confidence: float | None = None


class TTSRequest(BaseModel):
    """Text-to-speech request."""

    text: str
    voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    speed: float = 1.0  # 0.25 to 4.0


class TTSResponse(BaseModel):
    """Text-to-speech response."""

    audio_url: str
    text: str
    voice: str


@router.post("/recognize", response_model=RecognizeResponse)
async def recognize_speech(
    audio: UploadFile = File(...),
    language: str = "en",
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RecognizeResponse:
    """
    Convert speech to text using Whisper.

    - Supports multiple languages (auto-detect if not specified)
    - Returns transcribed text
    """
    openai_service = OpenAIService()

    try:
        # Read audio file
        audio_data = await audio.read()

        # Recognize speech
        result = await openai_service.transcribe_audio(
            audio_data=audio_data, language=language
        )

        return RecognizeResponse(
            text=result["text"],
            language=result.get("language", language),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Speech recognition failed: {str(e)}"
        )


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> TTSResponse:
    """
    Convert text to speech.

    - Supports Japanese pronunciation
    - Multiple voice options
    - Adjustable speed
    """
    openai_service = OpenAIService()

    try:
        audio_url = await openai_service.generate_tts(
            text=request.text, voice=request.voice, speed=request.speed
        )

        return TTSResponse(audio_url=audio_url, text=request.text, voice=request.voice)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
