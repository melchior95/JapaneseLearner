"""Japanese tokenization service using sudachipy."""
from __future__ import annotations

from typing import Any

try:
    from sudachipy import Dictionary, tokenizer

    SUDACHI_AVAILABLE = True
except ImportError:
    SUDACHI_AVAILABLE = False

try:
    import pykakasi

    PYKAKASI_AVAILABLE = True
except ImportError:
    PYKAKASI_AVAILABLE = False


class TokenizerService:
    """Japanese text tokenization and morphological analysis."""

    def __init__(self):
        if SUDACHI_AVAILABLE:
            self.tokenizer_obj = Dictionary().create()
            self.mode = tokenizer.Tokenizer.SplitMode.C
        else:
            self.tokenizer_obj = None

        # Initialize pykakasi for proper romanji conversion
        if PYKAKASI_AVAILABLE:
            self.kakasi = pykakasi.kakasi()
        else:
            self.kakasi = None

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
        Convert hiragana to romanji using pykakasi (proper conversion).
        Falls back to simplified mapping if pykakasi unavailable.

        Adopted from jidoujisho's KanaKit approach for robust conversion.
        """
        # Use pykakasi if available (handles all Japanese characters properly)
        if PYKAKASI_AVAILABLE and self.kakasi:
            try:
                # pykakasi converts hiragana/kanji to romanji
                result = ""
                for item in self.kakasi.convert(hiragana):
                    # item = {'orig': '..', 'kana': '..', 'kanji': '..', 'pron': '..', 'romaji': '..'}
                    if 'romaji' in item:
                        result += item['romaji']
                    elif 'kana' in item:
                        result += item['kana']
                    else:
                        result += item.get('orig', '')
                return result.lower()
            except Exception as e:
                print(f"Pykakasi conversion error: {e}, falling back to mapping")
                return self._to_romanji_mapping(hiragana)

        return self._to_romanji_mapping(hiragana)

    def _to_romanji_mapping(self, hiragana: str) -> str:
        """
        Fallback romanji conversion using comprehensive character mapping.
        Based on jidoujisho's hiragana-to-romaji conversion (improved).
        """
        # Comprehensive mapping including dakuten and special characters
        mapping = {
            # Vowels
            "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
            # K-row
            "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
            "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
            # S-row
            "さ": "sa", "し": "si", "す": "su", "せ": "se", "そ": "so",
            "ざ": "za", "じ": "zi", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
            # T-row
            "た": "ta", "ち": "ti", "つ": "tu", "て": "te", "と": "to",
            "だ": "da", "ぢ": "di", "づ": "du", "で": "de", "ど": "do",
            # N-row
            "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
            # H-row
            "は": "ha", "ひ": "hi", "ふ": "hu", "へ": "he", "ほ": "ho",
            "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
            "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
            # M-row
            "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
            # Y-row
            "や": "ya", "ゆ": "yu", "よ": "yo",
            # R-row
            "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
            # W-row
            "わ": "wa", "ゐ": "wi", "ゑ": "we", "を": "wo", "ん": "n",
            # Small tsu (sokuon) - typically handled differently
            "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ぁ": "a", "ぃ": "i",
            "ぅ": "u", "ぇ": "e", "ぉ": "o", "ゎ": "wa", "ゝ": "",
        }

        result = ""
        i = 0
        while i < len(hiragana):
            char = hiragana[i]

            # Handle small tsu (sokuon) - doubles the next consonant
            if char == "っ" and i + 1 < len(hiragana):
                next_char = hiragana[i + 1]
                next_romaji = mapping.get(next_char, next_char)
                # Add first consonant of next character
                if next_romaji:
                    result += next_romaji[0]
                i += 1
                continue

            # Regular character mapping
            result += mapping.get(char, char)
            i += 1

        return result
