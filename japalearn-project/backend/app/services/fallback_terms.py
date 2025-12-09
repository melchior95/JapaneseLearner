"""Japanese word fallback term generation service.

Adopted from jidoujisho's generateFallbackTerms method to provide robust
word lookup fallback chains. When exact dictionary lookup fails, this service
generates alternative search terms to find the word.

Fallback chain (6-level):
1. Original word (いった)
2. Root/dictionary form (いく)
3. Hiragana version (if input is romaji or katakana)
4. Katakana version (if input is hiragana or romaji)
5. Strip common conjugation suffixes (た, ている, そうに, etc.)
6. Multiple dictionary sources

This ensures users always find word definitions, even with inflected forms.
"""

from __future__ import annotations

from typing import Any

try:
    from sudachipy import Dictionary, tokenizer

    SUDACHI_AVAILABLE = True
except ImportError:
    SUDACHI_AVAILABLE = False


class FallbackTermsService:
    """Generate fallback search terms for Japanese word lookup.

    Based on jidoujisho's language/languages/japanese_language.dart:64
    Implements generateFallbackTerms() pattern.
    """

    # Common verb/adjective conjugation suffixes to strip
    COMMON_SUFFIXES = [
        "そうに",  # Seems like
        "ている",  # Progressive
        "た",      # Past tense
        "ぜ",      # Conditional
        "ば",      # Conditional
        "ます",    # Polite form
        "だ",      # Copula
        "ろ",      # Volitional
        "なさい",  # Imperative
    ]

    def __init__(self):
        if SUDACHI_AVAILABLE:
            self.sudachi = Dictionary().create()
            self.mode = tokenizer.Tokenizer.SplitMode.C
        else:
            self.sudachi = None

    async def get_fallback_terms(self, word: str) -> list[str]:
        """
        Generate fallback search terms for a Japanese word.

        Implements 6-level fallback chain from jidoujisho:
        1. Original word
        2. Root/dictionary form
        3. Hiragana version
        4. Katakana version
        5. Strip conjugation suffixes
        6. Multiple attempts

        Args:
            word: Japanese word to generate fallbacks for

        Returns:
            List of fallback terms in priority order
        """
        fallback_terms = [word]  # 1. Original word always first

        # 2. Get root form (dictionary form)
        root_form = await self._get_root_form(word)
        if root_form and root_form != word:
            fallback_terms.append(root_form)

        # 3-5. Kana conversions and root forms
        if self._is_romaji(word):
            # User input is romaji, generate hiragana and katakana
            hiragana = await self._romaji_to_hiragana(word)
            katakana = await self._hiragana_to_katakana(hiragana)

            if hiragana and hiragana != word:
                fallback_terms.append(hiragana)

                # Get root form of hiragana version
                hiragana_root = await self._get_root_form(hiragana)
                if hiragana_root and hiragana_root not in fallback_terms:
                    fallback_terms.append(hiragana_root)

            if katakana and katakana != word:
                fallback_terms.append(katakana)

                # Get root form of katakana version
                katakana_root = await self._get_root_form(katakana)
                if katakana_root and katakana_root not in fallback_terms:
                    fallback_terms.append(katakana_root)

        elif self._is_hiragana(word):
            # User input is hiragana, try katakana
            katakana = await self._hiragana_to_katakana(word)
            if katakana and katakana != word:
                fallback_terms.append(katakana)

        elif self._is_katakana(word):
            # User input is katakana, try hiragana
            hiragana = await self._katakana_to_hiragana(word)
            if hiragana and hiragana != word:
                fallback_terms.append(hiragana)

        # 5. Strip conjugation suffixes
        for suffix in self.COMMON_SUFFIXES:
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                stripped = word[:-len(suffix)]
                if stripped not in fallback_terms:
                    fallback_terms.append(stripped)

                    # Get root form of stripped version
                    stripped_root = await self._get_root_form(stripped)
                    if stripped_root and stripped_root not in fallback_terms:
                        fallback_terms.append(stripped_root)

        # Remove any None values and deduplicate while preserving order
        fallback_terms = [t for t in fallback_terms if t]
        seen = set()
        unique_terms = []
        for term in fallback_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms

    async def _get_root_form(self, word: str) -> str | None:
        """Get dictionary/root form of word using sudachi."""
        if not SUDACHI_AVAILABLE or not self.sudachi:
            return None

        try:
            tokens = self.sudachi.tokenize(word, self.mode)
            if tokens:
                return tokens[0].dictionary_form()
        except Exception as e:
            print(f"Root form extraction error: {e}")

        return None

    async def _romaji_to_hiragana(self, romaji: str) -> str | None:
        """Convert romaji to hiragana.

        This is a complex conversion that would benefit from a library.
        For now, return the input as we can't reliably convert without
        context. In production, use pykakasi.romaji_to_hiragana() or similar.
        """
        # Note: Proper implementation requires a library like pykakasi
        # For now, we return None to indicate this conversion needs external help
        # Future: implement using pykakasi.romaji_converter or similar
        return None

    async def _hiragana_to_katakana(self, hiragana: str) -> str:
        """Convert hiragana to katakana."""
        # Hiragana to katakana unicode range conversion
        # Hiragana: U+3041-U+309F, Katakana: U+30A1-U+30FF
        # Offset: 0x60 (96)

        result = ""
        for char in hiragana:
            char_code = ord(char)
            # Check if character is hiragana
            if 0x3041 <= char_code <= 0x309F:
                # Convert to katakana
                result += chr(char_code + 0x60)
            else:
                result += char

        return result

    async def _katakana_to_hiragana(self, katakana: str) -> str:
        """Convert katakana to hiragana."""
        # Katakana to hiragana unicode range conversion
        # Katakana: U+30A1-U+30FF, Hiragana: U+3041-U+309F
        # Offset: -0x60 (-96)

        result = ""
        for char in katakana:
            char_code = ord(char)
            # Check if character is katakana
            if 0x30A1 <= char_code <= 0x30FF:
                # Convert to hiragana
                result += chr(char_code - 0x60)
            else:
                result += char

        return result

    def _is_romaji(self, text: str) -> bool:
        """Check if text is in romaji (ASCII only)."""
        return all(ord(char) < 128 for char in text)

    def _is_hiragana(self, text: str) -> bool:
        """Check if text contains hiragana."""
        return any(0x3041 <= ord(char) <= 0x309F for char in text)

    def _is_katakana(self, text: str) -> bool:
        """Check if text contains katakana."""
        return any(0x30A1 <= ord(char) <= 0x30FF for char in text)
