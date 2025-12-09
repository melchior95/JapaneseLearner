"""OpenAI API service for GPT-4, Whisper, and TTS."""
from __future__ import annotations

import io
import uuid
from typing import Any, Optional

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.s3 import upload_file
from app.models.user import User

settings = get_settings()


class OpenAIService:
    """Handle OpenAI API interactions."""

    def __init__(self):
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None

    async def transcribe_audio(
        self, audio_data: bytes, language: str = "en"
    ) -> dict[str, Any]:
        """
        Transcribe audio using Whisper.

        Args:
            audio_data: Audio file bytes
            language: Language code (en, ja, etc.)

        Returns:
            Transcription result with text and language
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        # Create file-like object from bytes
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.mp3"  # Whisper needs a filename

        result = await self.client.audio.transcriptions.create(
            model=settings.openai_whisper_model, file=audio_file, language=language
        )

        return {"text": result.text, "language": language}

    async def generate_tts(
        self, text: str, voice: str = "alloy", speed: float = 1.0
    ) -> str:
        """
        Generate text-to-speech audio.

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speed of speech (0.25 to 4.0)

        Returns:
            URL to generated audio file
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        response = await self.client.audio.speech.create(
            model=settings.openai_tts_model, voice=voice, input=text, speed=speed
        )

        # Get audio data as bytes
        audio_data = response.content

        # Generate unique filename
        filename = f"tts/{uuid.uuid4()}.mp3"

        # Upload to S3/MinIO
        try:
            url = upload_file(audio_data, filename, content_type="audio/mpeg")
            return url
        except Exception as e:
            print(f"Error uploading TTS audio: {e}")
            raise ValueError(f"Failed to save TTS audio: {str(e)}")

    async def explain_grammar(
        self, sentence: str, detail_level: str = "comprehensive"
    ) -> dict[str, Any]:
        """
        Generate grammar explanation for a sentence.

        Args:
            sentence: Japanese sentence to explain
            detail_level: Level of detail (basic, intermediate, comprehensive)

        Returns:
            Explanation with grammar breakdown
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        system_prompt = """You are a Japanese language tutor helping students understand grammar.
Provide clear, detailed explanations with examples.
Break down sentences into grammatical components and explain each part.
Include cultural context when relevant."""

        user_prompt = f"""Explain this Japanese sentence in detail:
"{sentence}"

Detail level: {detail_level}

Provide:
1. Overall explanation of what the sentence means
2. Grammar breakdown (each part with its role and explanation)
3. Cultural context if relevant
4. Alternative ways to express the same meaning

Format your response as JSON with this structure:
{{
    "explanation": "overall explanation",
    "breakdown": [
        {{"part": "word/phrase", "role": "grammatical role", "explanation": "what it does"}},
        ...
    ],
    "cultural_context": "cultural notes",
    "alternatives": ["alternative phrasing 1", "alternative 2"]
}}
"""

        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        # Parse JSON response
        import json

        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            return {
                "explanation": response.choices[0].message.content,
                "breakdown": [],
                "cultural_context": None,
                "alternatives": [],
            }

    async def answer_question(
        self, question: str, context: Optional[dict] = None, user: Optional[User] = None
    ) -> dict[str, Any]:
        """
        Answer a question about Japanese language.

        Args:
            question: User's question
            context: Optional context (current sentence, word, etc.)
            user: Current user (optional)

        Returns:
            Answer with optional examples and audio
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        system_prompt = """You are a helpful Japanese language tutor.
Answer questions clearly and concisely with examples.
Be encouraging and patient. Provide practical usage examples."""

        user_prompt = question
        if context and context.get("current_sentence"):
            user_prompt = f"""Context: The student is studying this sentence:
"{context['current_sentence']}"

Question: {question}"""

        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        answer_text = response.choices[0].message.content

        return {
            "text": answer_text,
            "audio_url": None,  # TODO: Generate TTS
            "examples": [],
        }

    async def chat_response(
        self, conversation_id: str, message: str, session: Any
    ) -> dict[str, Any]:
        """
        Generate chat response in a conversation.

        Args:
            conversation_id: Conversation ID
            message: User's message
            session: Database session

        Returns:
            Response with text and optional audio
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        # Get conversation history
        from sqlalchemy import select

        from app.models.chat import ChatMessage

        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages_history = result.scalars().all()

        # Build conversation context
        conversation = [
            {
                "role": "system",
                "content": "You are a helpful Japanese language tutor. Be encouraging, clear, and provide practical examples.",
            }
        ]

        for msg in messages_history[-10:]:  # Last 10 messages for context
            conversation.append({"role": msg.role, "content": msg.content})

        conversation.append({"role": "user", "content": message})

        # Generate response
        response = await self.client.chat.completions.create(
            model=settings.openai_model, messages=conversation, temperature=0.7
        )

        answer_text = response.choices[0].message.content

        return {"text": answer_text, "audio_url": None}  # TODO: Generate TTS
