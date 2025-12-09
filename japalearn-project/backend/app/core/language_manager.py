"""Language management and registry.

Central place to register and access Language implementations.
Adopted from jidoujisho's AppModel plugin registry pattern.
"""

from __future__ import annotations

from typing import Optional

from app.core.language import Language
from app.languages.japanese import JapaneseLanguage


class LanguageManager:
    """Manages registered languages and provides access to language services."""

    def __init__(self):
        """Initialize language manager with default languages."""
        self._languages: dict[str, Language] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all registered languages.

        Called once on application startup.
        """
        if self._initialized:
            return

        # Register default languages
        await self.register_language(JapaneseLanguage())

        # Initialize all languages
        for language in self._languages.values():
            await language.initialize()

        self._initialized = True

    async def register_language(self, language: Language) -> None:
        """
        Register a language implementation.

        Args:
            language: Language instance to register
        """
        self._languages[language.language_code] = language

    def get_language(self, language_code: str) -> Optional[Language]:
        """
        Get language by code.

        Args:
            language_code: Language code (e.g., 'ja', 'zh', 'ko')

        Returns:
            Language instance or None if not registered
        """
        return self._languages.get(language_code)

    def get_available_languages(self) -> dict[str, Language]:
        """
        Get all registered languages.

        Returns:
            Dictionary of {language_code: Language}
        """
        return self._languages.copy()

    def get_language_names(self) -> dict[str, str]:
        """
        Get language names for UI display.

        Returns:
            Dictionary of {language_code: language_name}
        """
        return {
            code: lang.language_name
            for code, lang in self._languages.items()
        }

    def is_language_registered(self, language_code: str) -> bool:
        """Check if language is registered."""
        return language_code in self._languages

    async def get_word_info(self, language_code: str, word: str) -> Optional[dict]:
        """
        Get word information for a language.

        Args:
            language_code: Language code
            word: Word to look up

        Returns:
            Word information or None
        """
        language = self.get_language(language_code)
        if not language:
            return None

        return await language.get_word_info(word)

    def __repr__(self) -> str:
        languages = ", ".join(
            f"{code}({lang.language_name})"
            for code, lang in sorted(self._languages.items())
        )
        return f"LanguageManager({languages})"
