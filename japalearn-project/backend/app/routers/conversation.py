"""Conversation practice endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.db import get_session
from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User
from app.services.openai_service import OpenAIService
from app.services.tokenizer import TokenizerService
from app.services.translator import TranslatorService

router = APIRouter()


class ConversationStartRequest(BaseModel):
    """Start a new conversation with a scenario."""

    scenario_id: str
    system_prompt: str
    starter_message: str


class MessageRequest(BaseModel):
    """Send a message in a conversation."""

    conversation_id: str
    message: str
    language: str  # 'en' or 'ja'
    check_sentence: bool = False  # If True, GPT will check the sentence for errors


class WordToken(BaseModel):
    """Word token with metadata."""

    word: str
    reading: str | None = None
    romanji: str | None = None
    part_of_speech: str | None = None


class MessageResponse(BaseModel):
    """AI response with Japanese breakdown."""

    conversation_id: str
    message: str
    translation: str | None = None  # If user sent English
    words: list[WordToken] = []
    audio_url: str | None = None
    user_audio_url: str | None = None  # TTS for user's Japanese message


@router.post("/start", response_model=dict)
async def start_conversation(
    request: ConversationStartRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> dict:
    """
    Start a new conversation practice session with AI.

    Creates a conversation with the specified scenario and system prompt.
    """
    # Create conversation
    conversation = ChatConversation(
        user_id=current_user.id if current_user else None,
        context_sentence=request.scenario_id,  # Store scenario ID as context
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    # Add starter message from AI
    starter_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=request.starter_message,
    )
    session.add(starter_msg)
    await session.commit()

    # Tokenize starter message
    tokenizer = TokenizerService()
    words = []
    try:
        tokens = await tokenizer.tokenize(request.starter_message)
        words = [
            {
                "word": t["surface"],
                "reading": t.get("reading"),
                "romanji": t.get("romanji"),
                "part_of_speech": t.get("pos"),
            }
            for t in tokens
        ]
    except Exception as e:
        print(f"Tokenization error: {e}")

    return {
        "conversation_id": conversation.id,
        "starter_message": request.starter_message,
        "words": words,
    }


@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> MessageResponse:
    """
    Send a message in the conversation and get AI response.

    - If language is 'en', translates to Japanese first
    - AI responds in Japanese
    - Returns tokenized Japanese response
    """
    # Get conversation
    result = await session.execute(
        select(ChatConversation).where(ChatConversation.id == request.conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # If user sent English, translate to Japanese
    japanese_message = request.message
    translation = None

    if request.language == "en":
        translator = TranslatorService()
        trans_result = await translator.translate(
            text=request.message,
            source="en",
            target="ja",
            session=session,
            user=current_user,
        )
        japanese_message = trans_result.translated
        translation = japanese_message

    # Generate TTS for user's Japanese message (for pronunciation comparison)
    openai_service = OpenAIService()
    user_audio_url = None
    try:
        user_audio_url = await openai_service.generate_tts(japanese_message)
    except Exception as e:
        print(f"User TTS error: {e}")

    # Save user message (in Japanese)
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=japanese_message,
        audio_url=user_audio_url,  # Store user's TTS for pronunciation reference
    )
    session.add(user_msg)
    await session.commit()

    # Get conversation history for context
    history_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history = history_result.scalars().all()

    # Generate AI response

    # Build conversation for OpenAI
    messages = []

    # Different system prompt based on check_sentence mode
    if request.check_sentence:
        # Sentence checking mode
        system_prompt = """You are a Japanese language teacher checking a student's sentence.

Analyze the sentence they just said in Japanese. If it's correct:
- Start with "素晴らしい！" (Excellent!)
- Repeat what they said: "「[their sentence]」と言いましたね。" (You said "[their sentence]".)
- Give brief positive feedback in Japanese
- Then naturally continue the conversation in the scenario context

If there are errors:
- Gently point out the error in Japanese
- Provide the corrected version: "正しくは「[correct sentence]」と言います。" (The correct way is "[correct sentence]".)
- Explain briefly what was wrong
- Ask them to try again or continue the conversation

Keep it encouraging and conversational. Respond entirely in Japanese."""
    else:
        # Normal conversation mode
        system_prompt = """You are a helpful conversation partner for Japanese practice.
Respond naturally in Japanese.
Keep responses conversational and encourage the learner.
Use appropriate formality level based on the scenario.
Keep responses to 1-3 sentences."""

    messages.append({"role": "system", "content": system_prompt})

    # Add conversation history
    for msg in history[-10:]:  # Last 10 messages for context
        messages.append({"role": msg.role, "content": msg.content})

    # Get AI response
    try:
        response = await openai_service.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.8,
        )

        ai_message = response.choices[0].message.content

        # Save AI response
        assistant_msg = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_message,
        )
        session.add(assistant_msg)
        await session.commit()

        # Tokenize AI response
        tokenizer = TokenizerService()
        words = []
        try:
            tokens = await tokenizer.tokenize(ai_message)
            words = [
                WordToken(
                    word=t["surface"],
                    reading=t.get("reading"),
                    romanji=t.get("romanji"),
                    part_of_speech=t.get("pos"),
                )
                for t in tokens
            ]
        except Exception as e:
            print(f"Tokenization error: {e}")

        # Generate TTS for AI response
        audio_url = None
        try:
            audio_url = await openai_service.generate_tts(ai_message)
        except Exception as e:
            print(f"TTS error: {e}")

        return MessageResponse(
            conversation_id=conversation.id,
            message=ai_message,
            translation=translation if request.language == "en" else None,
            words=words,
            audio_url=audio_url,
            user_audio_url=user_audio_url,  # TTS for user's Japanese message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get conversation message history."""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    # Tokenize each message
    tokenizer = TokenizerService()
    response_messages = []

    for msg in messages:
        words = []
        try:
            tokens = await tokenizer.tokenize(msg.content)
            words = [
                {
                    "word": t["surface"],
                    "reading": t.get("reading"),
                    "romanji": t.get("romanji"),
                    "part_of_speech": t.get("pos"),
                }
                for t in tokens
            ]
        except Exception:
            pass

        response_messages.append(
            {
                "role": msg.role,
                "content": msg.content,
                "words": words,
                "audio_url": msg.audio_url,
                "created_at": msg.created_at.isoformat(),
            }
        )

    return response_messages


class ShadowCheckRequest(BaseModel):
    """Compare user's pronunciation with target sentence."""

    target_sentence: str
    spoken_sentence: str


class WordMatch(BaseModel):
    """Word matching result."""

    word: str
    correct: bool
    reading: str | None = None
    romanji: str | None = None


class ShadowCheckResponse(BaseModel):
    """Shadow practice result."""

    is_perfect: bool
    accuracy: float  # 0.0 to 1.0
    word_matches: list[WordMatch]
    message: str


@router.post("/shadow-check", response_model=ShadowCheckResponse)
async def shadow_check(
    request: ShadowCheckRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> ShadowCheckResponse:
    """
    Compare user's spoken sentence with target sentence for shadow practice.

    Returns word-by-word comparison with accuracy score.
    """
    import difflib
    from app.services.tokenizer import TokenizerService

    tokenizer = TokenizerService()

    # Normalize sentences for comparison
    target_normalized = request.target_sentence.strip()
    spoken_normalized = request.spoken_sentence.strip()

    # Tokenize both sentences
    try:
        target_tokens = await tokenizer.tokenize(target_normalized)
        spoken_tokens = await tokenizer.tokenize(spoken_normalized)
    except Exception as e:
        print(f"Tokenization error: {e}")
        # Fallback to character-level comparison
        target_tokens = [{"surface": c, "reading": "", "romanji": ""} for c in target_normalized]
        spoken_tokens = [{"surface": c, "reading": "", "romanji": ""} for c in spoken_normalized]

    # Extract word surfaces for comparison
    target_words = [t["surface"] for t in target_tokens]
    spoken_words = [t["surface"] for t in spoken_tokens]

    # Use difflib to find matching/differing parts
    matcher = difflib.SequenceMatcher(None, target_words, spoken_words)

    # Build word matches
    word_matches = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Correctly spoken words
            for i in range(i1, i2):
                token = target_tokens[i]
                word_matches.append(WordMatch(
                    word=token["surface"],
                    correct=True,
                    reading=token.get("reading"),
                    romanji=token.get("romanji"),
                ))
        elif tag in ('replace', 'delete'):
            # Incorrect or missing words
            for i in range(i1, i2):
                token = target_tokens[i]
                word_matches.append(WordMatch(
                    word=token["surface"],
                    correct=False,
                    reading=token.get("reading"),
                    romanji=token.get("romanji"),
                ))

    # Calculate accuracy
    correct_count = sum(1 for m in word_matches if m.correct)
    total_count = len(word_matches) if word_matches else 1
    accuracy = correct_count / total_count

    # Check if perfect
    is_perfect = accuracy >= 0.95  # 95% threshold for "perfect"

    # Generate feedback message
    if is_perfect:
        message = "完璧です！Perfect pronunciation!"
    elif accuracy >= 0.7:
        message = "もう少しです。Almost there! Try again."
    else:
        message = "もう一度挑戦してください。Please try again."

    return ShadowCheckResponse(
        is_perfect=is_perfect,
        accuracy=accuracy,
        word_matches=word_matches,
        message=message,
    )
