"""Grammar analysis and explanation service."""
from __future__ import annotations

from typing import Optional

from app.core.cache import cache_exists, cache_get, cache_set
from app.core.config import get_settings
from app.models.user import User
from app.routers.word import ExplainResponse, GrammarBreakdown
from app.services.openai_service import OpenAIService

settings = get_settings()


class GrammarService:
    """Provide grammar explanations and sentence analysis."""

    def __init__(self):
        self.openai_service = OpenAIService()

    async def explain_sentence(
        self,
        sentence: str,
        detail_level: str = "comprehensive",
        user: Optional[User] = None,
    ) -> ExplainResponse:
        """
        Generate comprehensive explanation of a Japanese sentence.

        Args:
            sentence: Japanese sentence to explain
            detail_level: Level of detail (basic, intermediate, comprehensive)
            user: Current user (optional)

        Returns:
            Detailed explanation with grammar breakdown
        """
        # Check cache
        cache_key = f"explain:{detail_level}:{sentence}"
        cached = await cache_get(cache_key)
        if cached:
            return ExplainResponse(**cached)

        # Use OpenAI for explanation
        try:
            result = await self.openai_service.explain_grammar(sentence, detail_level)

            response = ExplainResponse(
                sentence=sentence,
                explanation=result["explanation"],
                grammar_breakdown=[
                    GrammarBreakdown(**item) for item in result.get("breakdown", [])
                ],
                cultural_context=result.get("cultural_context"),
                alternative_phrasings=result.get("alternatives", []),
            )

            # Cache result
            await cache_set(cache_key, response.model_dump(), ttl=86400)  # 24 hours

            return response

        except Exception as e:
            # Fallback to basic explanation
            return ExplainResponse(
                sentence=sentence,
                explanation=f"Sentence: {sentence}\n\n[Grammar explanation service is currently unavailable]",
                grammar_breakdown=[],
            )
