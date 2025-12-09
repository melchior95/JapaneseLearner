"""Chat and Q&A endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.db import get_session
from app.models.user import User
from app.services.openai_service import OpenAIService

router = APIRouter()


class AskRequest(BaseModel):
    """Question request."""

    question: str
    context: dict | None = None
    # {"current_sentence": "...", "current_word": "..."}


class AskResponse(BaseModel):
    """Question answer response."""

    question: str
    answer: str
    audio_url: str | None = None
    related_examples: list[dict] | None = None


class ChatMessage(BaseModel):
    """Chat message."""

    role: str  # user, assistant
    content: str


class ChatRequest(BaseModel):
    """Chat request."""

    conversation_id: str | None = None
    message: str
    context: dict | None = None


class ChatResponse(BaseModel):
    """Chat response."""

    conversation_id: str
    message: str
    audio_url: str | None = None


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> AskResponse:
    """
    Ask a question about Japanese grammar, vocabulary, or usage.

    - Context-aware responses based on current learning material
    - Includes examples and explanations
    - Optional TTS audio response
    """
    openai_service = OpenAIService()

    try:
        answer = await openai_service.answer_question(
            question=request.question, context=request.context, user=current_user
        )

        return AskResponse(
            question=request.question,
            answer=answer["text"],
            audio_url=answer.get("audio_url"),
            related_examples=answer.get("examples"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


@router.post("/conversation", response_model=ChatResponse)
async def chat_conversation(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> ChatResponse:
    """
    Continue or start a chat conversation.

    - Maintains conversation history
    - Context-aware responses
    - Supports voice output
    """
    from app.models.chat import ChatConversation, ChatMessage

    # Get or create conversation
    if request.conversation_id:
        result = await session.execute(
            session.query(ChatConversation).filter(
                ChatConversation.id == request.conversation_id
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = ChatConversation(
            user_id=current_user.id if current_user else None,
            context_sentence=request.context.get("current_sentence")
            if request.context
            else None,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

    # Add user message
    user_message = ChatMessage(
        conversation_id=conversation.id, role="user", content=request.message
    )
    session.add(user_message)
    await session.commit()

    # Generate response
    openai_service = OpenAIService()
    response = await openai_service.chat_response(
        conversation_id=conversation.id, message=request.message, session=session
    )

    # Add assistant message
    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=response["text"],
        audio_url=response.get("audio_url"),
    )
    session.add(assistant_message)
    await session.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        message=response["text"],
        audio_url=response.get("audio_url"),
    )


@router.get("/conversation/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get conversation message history."""
    from sqlalchemy import select

    from app.models.chat import ChatMessage

    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        {
            "role": msg.role,
            "content": msg.content,
            "audio_url": msg.audio_url,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]
