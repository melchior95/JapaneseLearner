"""Japanese tokenization service using sudachipy."""
from __future__ import annotations

from typing import Any

try:
    from sudachipy import Dictionary, tokenizer

    SUDACHI_AVAILABLE = True
except ImportError:
    SUDACHI_AVAILABLE = False


class TokenizerService:
    """Japanese text tokenization and morphological analysis."""

    def __init__(self):
        if SUDACHI_AVAILABLE:
            self.tokenizer_obj = Dictionary().create()
            self.mode = tokenizer.Tokenizer.SplitMode.C
        else:
            self.tokenizer_obj = None

    async def tokenize(self, text: str) -> list[dict[str, Any]]:
        """
        Tokenize Japanese text into words with linguistic metadata.

        Args:
            text: Japanese text to tokenize

        Returns:
            List of token dictionaries with surface, reading, pos, etc.
        """
        if not SUDACHI_AVAILABLE or not self.tokenizer_obj:
            # Fallback: simple character-based splitting
            return self._fallback_tokenize(text)

        try:
            tokens = self.tokenizer_obj.tokenize(text, self.mode)
            result = []

            for token in tokens:
                # Get token information
                surface = token.surface()  # Original word
                reading = token.reading_form()  # Hiragana reading
                base_form = token.dictionary_form()  # Dictionary form
                pos = token.part_of_speech()[0]  # Part of speech

                # Convert reading to romanji (simplified)
                romanji = self._to_romanji(reading)

                result.append(
                    {
                        "surface": surface,
                        "reading": reading,
                        "romanji": romanji,
                        "base_form": base_form,
                        "pos": pos,
                    }
                )

            return result

        except Exception as e:
            print(f"Tokenization error: {e}")
            return self._fallback_tokenize(text)

    def _fallback_tokenize(self, text: str) -> list[dict[str, Any]]:
        """Simple fallback tokenization (character-based)."""
        return [
            {
                "surface": char,
                "reading": None,
                "romanji": None,
                "base_form": char,
                "pos": "unknown",
            }
            for char in text
            if char.strip()
        ]

    def _to_romanji(self, hiragana: str) -> str:
        """
        Convert hiragana to romanji (simplified mapping).
        In production, use a proper library like kakasi or pykakasi.
        """
        # This is a very simplified mapping - use a proper library in production
        mapping = {
            "あ": "a",
            "い": "i",
            "う": "u",
            "え": "e",
            "お": "o",
            "か": "ka",
            "き": "ki",
            "く": "ku",
            "け": "ke",
            "こ": "ko",
            "さ": "sa",
            "し": "shi",
            "す": "su",
            "せ": "se",
            "そ": "so",
            "た": "ta",
            "ち": "chi",
            "つ": "tsu",
            "て": "te",
            "と": "to",
            "な": "na",
            "に": "ni",
            "ぬ": "nu",
            "ね": "ne",
            "の": "no",
            "は": "ha",
            "ひ": "hi",
            "ふ": "fu",
            "へ": "he",
            "ほ": "ho",
            "ま": "ma",
            "み": "mi",
            "む": "mu",
            "め": "me",
            "も": "mo",
            "や": "ya",
            "ゆ": "yu",
            "よ": "yo",
            "ら": "ra",
            "り": "ri",
            "る": "ru",
            "れ": "re",
            "ろ": "ro",
            "わ": "wa",
            "を": "wo",
            "ん": "n",
            # Add more mappings as needed
        }

        result = ""
        for char in hiragana:
            result += mapping.get(char, char)

        return result
