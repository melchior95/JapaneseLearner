"""Language abstraction layer for multi-language support.

Adopted from jidoujisho's Language class to enable pluggable language support.
This allows the same framework to work with Japanese, Chinese, Korean, and other
languages with different NLP requirements.

Architecture:
- Language: Abstract base class
  - JapaneseLanguage: Japanese-specific implementation (sudachi)
  - ChineseLanguage: Chinese-specific (future, jieba)
  - KoreanLanguage: Korean-specific (future, MeCab)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class Language(ABC):
    """Abstract base class for language-specific NLP and resources.

    Each Language implementation provides:
    - Text tokenization
    - Text-to-words conversion
    - Fallback term generation for dictionary lookups
    - Part-of-speech tagging
    - Root form extraction
    """

    def __init__(
        self,
        language_code: str,
        language_name: str,
        country_code: str = "",
    ):
        """
        Initialize language instance.

        Args:
            language_code: ISO 639-1 code (e.g., 'ja', 'zh', 'ko')
            language_name: Display name (e.g., '日本語', '中文', '한국어')
            country_code: Optional country code (e.g., 'JP', 'CN')
        """
        self.language_code = language_code
        self.language_name = language_name
        self.country_code = country_code
        self.dictionaries = []  # DictionaryFormat instances bound to this language

    async def initialize(self) -> None:
        """Initialize language resources (NLP models, etc.).

        Called once on application startup. Load heavy resources here.
        """
        pass

    @abstractmethod
    async def tokenize(self, text: str) -> list[dict[str, Any]]:
        """
        Tokenize text into words with linguistic metadata.

        Returns list of token dictionaries with:
        - surface: Original text
        - reading: Hiragana/pinyin reading (if applicable)
        - romanji: Romanized reading
        - base_form: Dictionary form
        - pos: Part of speech
        - lemma: Root/base form

        Args:
            text: Text to tokenize

        Returns:
            List of token dictionaries
        """
        pass

    @abstractmethod
    async def text_to_words(self, text: str) -> list[str]:
        """
        Convert text to list of words for text selection.

        Similar to tokenize() but returns just the words without metadata.

        Args:
            text: Text to convert

        Returns:
            List of words
        """
        pass

    @abstractmethod
    async def get_root_form(self, word: str) -> str:
        """
        Get dictionary/root form of a word.

        For verbs: いった → いく
        For kanji: 食べる → 食べる (already root)

        Args:
            word: Word to get root form for

        Returns:
            Root/dictionary form
        """
        pass

    @abstractmethod
    async def get_fallback_terms(self, word: str) -> list[str]:
        """
        Generate fallback search terms for dictionary lookup.

        6-level chain:
        1. Original word
        2. Root form
        3. Kana conversions
        4. Katakana/Hiragana variants
        5. Strip conjugation suffixes
        6. Multiple sources

        Args:
            word: Word to generate fallbacks for

        Returns:
            List of fallback terms in priority order
        """
        pass

    async def get_word_info(self, word: str, dictionaries: Optional[list] = None) -> dict[str, Any]:
        """
        Get word information from bound dictionaries.

        Uses fallback chain to find word in any bound dictionary.

        Args:
            word: Word to look up
            dictionaries: Optional override list of DictionaryFormat instances

        Returns:
            Word information dictionary or None if not found
        """
        dicts = dictionaries or self.dictionaries
        fallback_terms = await self.get_fallback_terms(word)

        for term in fallback_terms:
            for dict_format in dicts:
                result = await dict_format.search(term)
                if result:
                    return result

        return None

    def get_identifier(self) -> str:
        """Get unique identifier for this language (e.g., 'ja', 'zh_CN')."""
        if self.country_code:
            return f"{self.language_code}_{self.country_code}"
        return self.language_code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.language_code})"
