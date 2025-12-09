"""Japanese language support implementation.

Ported from jidoujisho's JapaneseLanguage class.
Uses sudachi for tokenization and morphological analysis.
"""

from __future__ import annotations

from typing import Any

from app.core.language import Language
from app.services.fallback_terms import FallbackTermsService
from app.services.tokenizer import TokenizerService

try:
    from sudachipy import Dictionary, tokenizer

    SUDACHI_AVAILABLE = True
except ImportError:
    SUDACHI_AVAILABLE = False


class JapaneseLanguage(Language):
    """Japanese language support using sudachi tokenizer.

    Ported from jidoujisho/chisa/lib/language/languages/japanese_language.dart
    """

    def __init__(self):
        super().__init__(
            language_code="ja",
            language_name="日本語",
            country_code="JP",
        )
        self.tokenizer_service: TokenizerService | None = None
        self.fallback_service: FallbackTermsService | None = None
        self.sudachi = None
        self.sudachi_mode = None

    async def initialize(self) -> None:
        """Initialize Japanese NLP services."""
        if SUDACHI_AVAILABLE:
            self.sudachi = Dictionary().create()
            self.sudachi_mode = tokenizer.Tokenizer.SplitMode.C

        self.tokenizer_service = TokenizerService()
        self.fallback_service = FallbackTermsService()

    async def tokenize(self, text: str) -> list[dict[str, Any]]:
        """
        Tokenize Japanese text into words with linguistic metadata.

        Uses sudachi for morphological analysis.

        Args:
            text: Japanese text to tokenize

        Returns:
            List of token dictionaries
        """
        if not self.tokenizer_service:
            await self.initialize()

        return await self.tokenizer_service.tokenize(text)

    async def text_to_words(self, text: str) -> list[str]:
        """
        Convert Japanese text to list of words.

        Handles space delimiters and bunsetsu (phrase) units.

        Args:
            text: Japanese text

        Returns:
            List of words
        """
        tokens = await self.tokenize(text)
        words = []

        for token in tokens:
            surface = token.get("surface", "")
            if surface.strip():  # Skip whitespace
                words.append(surface)

        return words

    async def get_root_form(self, word: str) -> str:
        """
        Get dictionary/root form of Japanese word.

        Examples:
        - いった (past) → いく (verb root)
        - 食べた (past) → 食べる (verb root)
        - 走っている (progressive) → 走る (verb root)

        Uses sudachi's dictionary_form() method.

        Args:
            word: Japanese word

        Returns:
            Dictionary/root form
        """
        if not SUDACHI_AVAILABLE or not self.sudachi:
            return word

        try:
            tokens = self.sudachi.tokenize(word, self.sudachi_mode)
            if tokens:
                return tokens[0].dictionary_form()
        except Exception as e:
            print(f"Root form extraction error: {e}")

        return word

    async def get_fallback_terms(self, word: str) -> list[str]:
        """
        Generate fallback search terms for Japanese word lookup.

        6-level chain (from jidoujisho's generateFallbackTerms):
        1. Original word
        2. Root/dictionary form
        3. Hiragana version
        4. Katakana version
        5. Strip conjugation suffixes
        6. Multiple dictionary sources

        Args:
            word: Japanese word

        Returns:
            List of fallback terms in priority order
        """
        if not self.fallback_service:
            await self.initialize()

        return await self.fallback_service.get_fallback_terms(word)

    def is_romaji(self, text: str) -> bool:
        """Check if text is in romaji (ASCII only)."""
        return all(ord(char) < 128 for char in text)

    def is_hiragana(self, text: str) -> bool:
        """Check if text contains hiragana."""
        return any(0x3041 <= ord(char) <= 0x309F for char in text)

    def is_katakana(self, text: str) -> bool:
        """Check if text contains katakana."""
        return any(0x30A1 <= ord(char) <= 0x30FF for char in text)

    def is_kanji(self, char: str) -> bool:
        """Check if character is kanji."""
        code = ord(char)
        # CJK Unified Ideographs and other kanji ranges
        return (
            (0x4E00 <= code <= 0x9FFF) or  # CJK Unified Ideographs
            (0x3400 <= code <= 0x4DBF) or  # CJK Extension A
            (0x20000 <= code <= 0x2A6DF)   # CJK Extension B
        )

    async def has_kanji(self, text: str) -> bool:
        """Check if text contains kanji."""
        return any(self.is_kanji(char) for char in text)

    async def to_hiragana(self, text: str) -> str:
        """
        Convert katakana to hiragana.

        Adopted from jidoujisho's kana_kit.toHiragana().

        Args:
            text: Text potentially containing katakana

        Returns:
            Text with katakana converted to hiragana
        """
        # Katakana to hiragana conversion: subtract 0x60 (96)
        result = ""
        for char in text:
            code = ord(char)
            if 0x30A1 <= code <= 0x30FF:  # Katakana range
                result += chr(code - 0x60)
            else:
                result += char
        return result

    async def to_katakana(self, text: str) -> str:
        """
        Convert hiragana to katakana.

        Adopted from jidoujisho's kana_kit.toKatakana().

        Args:
            text: Text potentially containing hiragana

        Returns:
            Text with hiragana converted to katakana
        """
        # Hiragana to katakana conversion: add 0x60 (96)
        result = ""
        for char in text:
            code = ord(char)
            if 0x3041 <= code <= 0x309F:  # Hiragana range
                result += chr(code + 0x60)
            else:
                result += char
        return result
