# JapaLearn vs Jidoujisho: Comprehensive Analysis & Integration Guide

## Executive Summary

**Jidoujisho** is a mature, battle-tested Flutter mobile app (16,570+ LOC) with proven patterns for language learning. **JapaLearn** is a modern web stack (FastAPI + React) targeting the same problem space. This document identifies critical gaps in JapaLearn and recommends adopting proven patterns from jidoujisho to ensure production readiness.

**Key Findings:**
- ✅ JapaLearn has solid modern tech (FastAPI, React, Docker)
- ⚠️ JapaLearn's NLP implementation is immature (simplified romanji mapping, limited fallbacks)
- ⚠️ Dictionary/word lookup lacks persistence patterns and caching strategy
- ⚠️ No multi-language support framework (jidoujisho supports 5 languages with pluggable architecture)
- ⚠️ Frontend state management is minimal; missing comprehensive progress tracking

---

## Part 1: Architecture Comparison

### Jidoujisho Architecture (Mature)

**Pattern:** Plugin-based, modular monolith
- **State Management:** Provider (ChangeNotifier) with AppModel as single source of truth
- **Data Persistence:** ObjectBox (NoSQL) + SharedPreferences
- **Language Support:** Pluggable Language class with 5 implementations
- **Dictionary System:** Pluggable DictionaryFormat with 4+ implementations
- **Media System:** Pluggable MediaSource abstraction layer
- **Core Pattern:** Dependency injection via AppModel initialization

**Strengths:**
- Proven on production (1.1+ releases)
- Multi-language support framework
- Offline-first architecture (no required APIs)
- Pluggable text processing pipelines
- Robust NLP fallback chains
- Comprehensive word lookup with caching

### JapaLearn Architecture (Current)

**Pattern:** Stateless REST API + SPA Frontend
- **Backend State:** Stateless FastAPI, single PostgreSQL database
- **Frontend State:** TanStack Query (React Query) + hooks
- **Language Support:** Hardcoded to Japanese only
- **Dictionary System:** Inline JDictService (no abstraction)
- **NLP Pipeline:** Single TokenizerService with basic fallback
- **Data Persistence:** PostgreSQL only; no caching layer

**Strengths:**
- Modern async framework (FastAPI)
- Docker-ready infrastructure
- REST API design
- React component reusability

**Weaknesses:**
- Stateless API means repeated work per request
- No intermediate caching between API and database
- NLP is hardcoded to Japanese (not extensible)
- Frontend state management minimal

---

## Part 2: NLP & Text Processing Comparison

### Jidoujisho NLP (Battle-Tested ✅)

**Core Tools:**
- **MeCab** for Japanese (via mecab_dart package)
- **Ve** for enhanced morphology (ve_dart)
- **KanaKit** for kana/romaji conversion
- **Language-specific fallbacks** (hiragana↔katakana, root forms, suffix stripping)

**Key Pattern:**
```dart
// jidoujisho/chisa/lib/language/languages/japanese_language.dart
class JapaneseLanguage extends Language {
  Future<List<String>> generateFallbackTerms(String searchTerm) async {
    // 1. Get root form via MeCab
    // 2. Convert hiragana ↔ katakana ↔ romaji
    // 3. Strip common suffixes (そうに, etc.)
    // 4. Return multiple fallback queries for dict lookup
  }
}
```

**Why This Matters:**
- User searches "いった" → finds "いく" (root) → finds definitions
- User searches "walking" (romaji) → converts to hiragana → finds match
- **Graceful degradation**: Always returns something useful

### JapaLearn NLP (Needs Improvement ⚠️)

**Current Implementation:**
```python
# japalearn-project/backend/app/services/tokenizer.py
class TokenizerService:
  async def tokenize(self, text: str) -> list[dict]:
    # 1. Use sudachipy (good choice)
    # 2. Convert to hiragana (basic mapping, ~50 chars)
    # 3. FALLBACK: Character-based splitting (loses meaning)
```

**Problems:**
1. **Incomplete romanji mapping:** Only ~50 kana, missing dakuten, combined sounds
   ```python
   # Missing: が,ぎ,ぐ,げ,ご,ぎゃ,etc.
   "か": "ka",  # Works
   "が": ???     # Not in mapping!
   ```

2. **No fallback chains:** If word not found → gives up
3. **No root form extraction:** Each verb form is separate dictionary lookup
4. **Character-based fallback useless:** "こんにちは" → ["こ", "ん", "に", "ち", "は"]

### Integration Recommendation

**Adopt jidoujisho's multi-level fallback strategy:**

```python
# Pseudocode for improved japalearn tokenizer
class ImprovedTokenizer:
    async def get_search_terms(self, word: str) -> list[str]:
        fallback_terms = []

        # 1. Original word
        fallback_terms.append(word)

        # 2. Root form via sudachi
        root = await self.get_root_form(word)
        if root != word:
            fallback_terms.append(root)

        # 3. Kana conversions
        if is_romaji(word):
            fallback_terms.append(hiragana(word))
            fallback_terms.append(katakana(word))
        elif is_hiragana(word):
            fallback_terms.append(katakana(word))

        # 4. Strip suffixes (conjugations, auxiliaries)
        for suffix in COMMON_SUFFIXES:  # そうに, ている, etc.
            if word.endswith(suffix):
                fallback_terms.append(word[:-len(suffix)])

        return fallback_terms
```

---

## Part 3: Dictionary & Word Lookup Comparison

### Jidoujisho Dictionary System (Production-Ready ✅)

**Architecture:**
```
DictionaryFormat (abstract)
├── YomichanTermBankFormat (Yomichan JSON)
├── CCCEDICTSimplified (CCCEDICT CSV)
├── NaverDictionaryFormat
└── [User can add custom formats]

Language (abstract)
├── JapaneseLanguage
│   ├── dictionaries: YomichanTermBankFormat[]
│   └── fallbackTerms() → generator
├── ChineseSimplifiedLanguage
│   ├── dictionaries: CCCEDICTSimplified[]
├── KoreanLanguage
└── etc.
```

**Key Features:**
1. **Pluggable dictionary formats** (user adds Yomichan archives)
2. **Per-language dictionary binding** (each language has its own dict set)
3. **ObjectBox indexing** for fast lookups
4. **In-memory caching** with generational updates
5. **Dictionary-specific metadata** (pitch accents, JMdict sources)

**Lookup Flow:**
```
user_click("いった")
  → fallbackTerms = ["いった", "いく", "iku", "イク"]
  → for term in fallbackTerms:
      → search_all_dictionaries(term)
      → return first_match_with_metadata()
```

### JapaLearn Dictionary System (Basic ⚠️)

**Architecture:**
```
JDictService
├── get_word_info(word) → cache or DB lookup
└── _track_word_view() → user progress

Models:
├── JapaneseWord (word, reading, definition)
├── WordExample (sample sentences)
└── UserWordProgress (tracking)
```

**Problems:**
1. **Single hardcoded service** (no abstraction for other languages)
2. **Redis cache only** (no disk persistence for offline)
3. **No fallback terms:** Dictionary lookup fails if exact match missing
4. **No metadata:** No source attribution, no JLPT levels populated
5. **Database-only:** Must have PostgreSQL running; no offline support

### Integration Recommendation

**Adopt jidoujisho's pluggable dictionary system:**

```python
# New architecture for japalearn
from abc import ABC, abstractmethod

class DictionaryFormat(ABC):
    """Base for pluggable dictionary loaders."""

    @abstractmethod
    async def load_dictionary(self, file_path: str) -> dict:
        """Load dict from archive/file."""
        pass

    @abstractmethod
    async def search(self, term: str) -> list[WordEntry]:
        """Search for term in this format's data."""
        pass

class YomichanFormat(DictionaryFormat):
    """Yomichan JSON archive support (used by jidoujisho)."""

    async def load_dictionary(self, archive_path: str):
        # Parse Yomichan format (same as jidoujisho)
        pass

class LanguageProfile(ABC):
    """Bind dictionaries + NLP to language."""

    def __init__(self, language_code: str):
        self.dictionaries: list[DictionaryFormat] = []
        self.tokenizer = TokenizerService(language_code)

    async def get_word_info(self, word: str) -> WordInfo:
        fallback_terms = await self.tokenizer.get_search_terms(word)
        for term in fallback_terms:
            for dict_format in self.dictionaries:
                results = await dict_format.search(term)
                if results:
                    return results[0]
        return WordInfo(word=word, definition="Not found")

# Usage
japanese_profile = LanguageProfile("ja")
japanese_profile.dictionaries = [
    YomichanFormat("dictionary_ja.zip"),
    JMdictFormat("jmdict.db"),
]

word_info = await japanese_profile.get_word_info("いった")
```

---

## Part 4: State Management & Persistence Comparison

### Jidoujisho State Management (Proven ✅)

**Pattern:** Centralized AppModel with Provider

```dart
class AppModel with ChangeNotifier {
  // Single source of truth
  late SharedPreferences _sharedPreferences;  // Persistent settings
  late ObjectBox _objectBox;                   // Local DB for words, history
  late AudioHandler _audioHandler;             // Audio state

  // Pluggable systems registered here
  final Map<String, Language> _availableLanguages = {};
  final Map<String, DictionaryFormat> _dictionaryFormats = {};
  final Map<MediaType, MediaSource> _mediaSources = {};

  // Subscribe to changes
  ValueNotifier<bool> dictionaryUpdateFlipflop = ValueNotifier(false);

  void notifyListeners() {
    // UI rebuilds via Provider<AppModel>.watch()
  }
}
```

**Benefits:**
- Single source of truth (no stale state)
- Offline-first (ObjectBox = local DB)
- No network dependency
- Plugin registration centralized
- UI rebuilds automatically on state changes

### JapaLearn State Management (Frontend-Heavy ⚠️)

**Pattern:** Stateless API + TanStack Query

```typescript
// Frontend (React)
const { data, isLoading } = useQuery({
  queryKey: ['word', 'こんにちは'],
  queryFn: async () => {
    const res = await fetch('/api/v1/word/こんにちは/info');
    return res.json();
  },
});

// Backend (FastAPI)
@app.get("/api/v1/word/{word}/info")
async def get_word_info(word: str, session: AsyncSession):
    # On every request: cache → DB → return
    # No persistent state
```

**Problems:**
1. **Distributed state:** Frontend knows about caching, backend doesn't coordinate
2. **Network required:** Every action hits API (no offline mode)
3. **No unified settings:** User preferences scattered (localStorage, cookies, DB)
4. **Cache miss = slow:** No fallback, just waits for DB
5. **Plugin system missing:** Hard to add language support

### Integration Recommendation

**Adopt hybrid approach (jidoujisho offline + API for sync):**

```python
# Backend: Implement a state layer
class AppState:
    """Central state management (like jidoujisho's AppModel)."""

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.cache = redis
        self.languages: dict[str, LanguageProfile] = {}
        self.dictionaries: dict[str, DictionaryFormat] = {}

    async def initialize(self):
        """Called on app startup."""
        # Load all registered languages
        self.languages = {
            "ja": await JapaneseLanguage.load(),
            "zh": await ChineseLanguage.load(),
        }
        # Load all dictionaries into memory
        for lang in self.languages.values():
            lang.dictionaries = await self._load_dicts_for_lang(lang)

# Frontend: React component with local state + server sync
function WordLookup({ word }: { word: string }) {
    const [localHistory, setLocalHistory] = useLocalStorage('word_history', []);

    // Query from backend (cached for 1 hour)
    const { data: wordInfo } = useQuery({
        queryKey: ['word', word],
        queryFn: () => fetchWordInfo(word),
        staleTime: 1000 * 60 * 60, // 1 hour
    });

    const handleLookup = () => {
        // Save locally
        setLocalHistory([word, ...localHistory]);
        // Sync with server (fire-and-forget)
        trackWordView(word).catch(console.warn);
    };

    return <div>{wordInfo?.definition}</div>;
}
```

---

## Part 5: Multi-Language Support Comparison

### Jidoujisho (5 Languages, Extensible ✅)

**Supported:**
- Japanese (MeCab + KanaKit)
- Chinese Simplified (Jieba via Chaquopy)
- Chinese Traditional (CCCEDICT)
- Korean (MeCab)
- English (basic)

**Extension Pattern:**
```dart
// To add Vietnamese (example):
class VietnameseLanguage extends Language {
  @override
  Future<void> initialiseLanguage() async {
    // Load Vietnamese tokenizer
    this.tokenizer = await PyflutterVi.init();
  }

  @override
  FutureOr<List<String>> textToWords(String text) {
    return tokenizer.segment(text);
  }
}

// Register in AppModel
_availableLanguages['vi'] = VietnameseLanguage();
```

### JapaLearn (Japanese Only ⚠️)

**Hardcoded to Japanese:**
```python
# No abstraction; specific to Japanese only
class TokenizerService:
    def __init__(self):
        self.tokenizer = Dictionary().create()  # sudachi (JP only)

    async def tokenize(self, text: str) -> list[dict]:
        # ... hardcoded for Japanese
```

**Adding Chinese support would require:**
- Refactor TokenizerService → abstract base
- Create JapaneseSudachiTokenizer, ChineseJiebaTokenizer
- Create Language abstraction
- Update all routers to use Language system

### Integration Recommendation

**Adopt jidoujisho's Language abstraction:**

```python
from abc import ABC, abstractmethod

class Language(ABC):
    """Language-specific NLP and resources."""

    def __init__(self, language_code: str, language_name: str):
        self.language_code = language_code
        self.language_name = language_name
        self.dictionaries: list[DictionaryFormat] = []

    @abstractmethod
    async def tokenize(self, text: str) -> list[Token]:
        """Tokenize text into words."""
        pass

    @abstractmethod
    async def get_fallback_terms(self, word: str) -> list[str]:
        """Generate fallback search terms."""
        pass

    async def get_word_info(self, word: str) -> WordInfo:
        """Lookup word using language-specific fallbacks."""
        terms = await self.get_fallback_terms(word)
        for term in terms:
            for dict_format in self.dictionaries:
                result = await dict_format.search(term)
                if result:
                    return result
        return WordInfo(word=word, definition="Not found")

class JapaneseSudachi(Language):
    """Japanese with sudachi tokenizer."""

    async def tokenize(self, text: str) -> list[Token]:
        # sudachi tokenization
        pass

    async def get_fallback_terms(self, word: str) -> list[str]:
        # Hiragana/katakana/romaji conversions
        # Root form extraction
        pass

class ChineseJieba(Language):
    """Chinese with jieba tokenizer."""

    async def tokenize(self, text: str) -> list[Token]:
        # jieba tokenization
        pass

    async def get_fallback_terms(self, word: str) -> list[str]:
        # Simplified ↔ traditional, pinyin, etc.
        pass

# In AppState
class AppState:
    def __init__(self):
        self.languages = {
            "ja": JapaneseSudachi(),
            "zh": ChineseJieba(),
        }

    async def get_word_info(self, language: str, word: str) -> WordInfo:
        return await self.languages[language].get_word_info(word)
```

---

## Part 6: Critical Missing Features in JapaLearn

| Feature | Jidoujisho | JapaLearn | Priority |
|---------|-----------|-----------|----------|
| **Offline support** | ✅ (ObjectBox) | ❌ API-only | CRITICAL |
| **Multiple language support** | ✅ (5 languages) | ❌ JP only | CRITICAL |
| **Pluggable dict formats** | ✅ (Yomichan, CCCEDICT) | ❌ DB only | HIGH |
| **Fallback term generation** | ✅ (6-level chain) | ⚠️ (basic) | HIGH |
| **User word history/progress** | ✅ (ObjectBox) | ✅ (PostgreSQL) | MEDIUM |
| **Pitch accent data** | ✅ (Kanjium) | ❌ | MEDIUM |
| **AnkiDroid export** | ✅ (native API) | ❌ | MEDIUM |
| **Media mining (video/manga)** | ✅ | ❌ (future) | LOW |

---

## Part 7: Implementation Roadmap for JapaLearn

### Phase 1: Foundational Improvements (Weeks 1-3)

**1.1 Create Language Abstraction**
- [ ] `Language` abstract base class
- [ ] `JapaneseLanguage` implementation with sudachi
- [ ] Move tokenizer logic into Language
- [ ] Create `LanguageRegistry` in AppState

**1.2 Improve NLP Tokenizer**
- [ ] Fix romanji mapping (use `pykakasi` library)
- [ ] Implement multi-level fallback chain (like jidoujisho)
- [ ] Add root form extraction
- [ ] Add suffix stripping for verb conjugations

**1.3 Create AppState Pattern**
- [ ] Central `AppState` class (like jidoujisho's AppModel)
- [ ] Dependency injection: `@app.dependency`
- [ ] Plugin registry for Languages, Dictionaries, Services
- [ ] Initialize on startup, reuse for all requests

### Phase 2: Dictionary System Improvements (Weeks 4-5)

**2.1 Create DictionaryFormat Abstraction**
- [ ] `DictionaryFormat` abstract base class
- [ ] `YomichanFormat` (import from jidoujisho's format)
- [ ] Support for loading .zip archives
- [ ] Persistent caching (PostgreSQL cache table)

**2.2 Bind Dictionaries to Languages**
- [ ] `Language.dictionaries: list[DictionaryFormat]`
- [ ] Load user-imported dictionaries on startup
- [ ] Multi-dictionary fallback chain

**2.3 Improve Caching Layer**
- [ ] Add Redis caching layer before PostgreSQL
- [ ] Implement cache invalidation strategy
- [ ] Warm cache on app startup with popular words

### Phase 3: Multi-Language Support (Weeks 6-7)

**3.1 Add Chinese Support**
- [ ] `ChineseLanguage` with jieba tokenizer
- [ ] Simplified ↔ Traditional conversion
- [ ] CCCEDICT dictionary format (use jidoujisho's)
- [ ] Pinyin romanization

**3.2 Add Korean Support**
- [ ] `KoreanLanguage` with MeCab
- [ ] Hangul-to-romanization
- [ ] Naver dictionary format (use jidoujisho's)

**3.3 Create Language Picker**
- [ ] Frontend: Language selection dropdown
- [ ] Backend: Route requests to correct Language
- [ ] Persist user language preference

### Phase 4: Offline Support (Weeks 8-9)

**4.1 SQLite Offline Database**
- [ ] Create SQLite schema for words/dictionaries
- [ ] Sync from PostgreSQL → SQLite on login
- [ ] Fallback: Query SQLite if PostgreSQL unreachable

**4.2 Progressive Web App (PWA)**
- [ ] Add service worker for offline mode
- [ ] Cache critical resources
- [ ] IndexedDB for offline word cache

### Phase 5: Production Hardening (Weeks 10+)

**5.1 Testing**
- [ ] Unit tests for Language implementations
- [ ] Integration tests for dictionary lookups
- [ ] Fallback chain tests

**5.2 Performance**
- [ ] Profile tokenizer performance
- [ ] Optimize dictionary search (B-tree indexing)
- [ ] Benchmark against jidoujisho

**5.3 Data Import**
- [ ] Yomichan archive importer
- [ ] JMdict loader
- [ ] Migration from jidoujisho (export history, words)

---

## Part 8: Specific Code Migrations from Jidoujisho

### 1. Japanese Fallback Term Generation

**From jidoujisho (proven):**
```dart
// jidoujisho/chisa/lib/language/languages/japanese_language.dart:64
FutureOr<List<String>> generateFallbackTerms(String searchTerm) async {
    List<String> fallbackTerms = [];

    String rootForm = await getRootForm(searchTerm);
    if (rootForm != searchTerm) {
        fallbackTerms.add(rootForm);
    }

    if (kanaKit.isRomaji(searchTerm)) {
        String hiragana = kanaKit.toHiragana(searchTerm);
        String katakana = kanaKit.toKatakana(searchTerm);
        String hiraganaFallback = await getRootForm(hiragana);
        String katakanaFallback = await getRootForm(katakana);

        fallbackTerms.add(hiragana);
        if (hiraganaFallback != hiragana) {
            fallbackTerms.add(hiraganaFallback);
        }
        fallbackTerms.add(katakana);
        if (katakanaFallback != katakana) {
            fallbackTerms.add(katakanaFallback);
        }
    } else {
        if (kanaKit.isHiragana(searchTerm)) {
            fallbackTerms.add(kanaKit.toKatakana(searchTerm));
        }
        if (kanaKit.isKatakana(searchTerm)) {
            fallbackTerms.add(kanaKit.toHiragana(searchTerm));
        }
        if (searchTerm.length > 4) {
            if (searchTerm.endsWith("そうに")) {
                fallbackTerms.add(searchTerm.substring(0, searchTerm.length - 3));
            }
            fallbackTerms.add(searchTerm.substring(0, searchTerm.length - 2));
        }
    }

    return fallbackTerms;
}
```

**Python equivalent for JapaLearn:**
```python
# Requires: pykakasi, sudachi
import pykakasi

class JapaneseFallbackGenerator:
    def __init__(self):
        self.sudachi = Dictionary().create()
        self.kakasi = pykakasi.kakasi()

    async def get_fallback_terms(self, word: str) -> list[str]:
        """Generate fallback search terms (6-level chain)."""
        terms = [word]

        # 1. Root form
        root = await self.get_root_form(word)
        if root != word:
            terms.append(root)

        # 2. Kana conversions
        if self.is_romaji(word):
            hiragana = await self.to_hiragana(word)
            katakana = await self.to_katakana(word)
            terms.append(hiragana)
            terms.append(katakana)

            hiragana_root = await self.get_root_form(hiragana)
            if hiragana_root != hiragana:
                terms.append(hiragana_root)

            katakana_root = await self.get_root_form(katakana)
            if katakana_root != katakana:
                terms.append(katakana_root)
        elif self.is_hiragana(word):
            katakana = await self.to_katakana(word)
            terms.append(katakana)
        elif self.is_katakana(word):
            hiragana = await self.to_hiragana(word)
            terms.append(hiragana)

        # 3. Suffix stripping (verb conjugations)
        for suffix in ["そうに", "ている", "た", "だ"]:
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                terms.append(word[:-len(suffix)])

        return terms

    async def get_root_form(self, word: str) -> str:
        """Get dictionary form via sudachi."""
        tokens = self.sudachi.tokenize(word, Tokenizer.SplitMode.C)
        if tokens:
            return tokens[0].dictionary_form()
        return word

    async def to_hiragana(self, text: str) -> str:
        """Convert to hiragana."""
        # Use pykakasi or similar
        return self.kakasi.convert(text)

    async def to_katakana(self, text: str) -> str:
        """Convert to katakana."""
        hiragana = await self.to_hiragana(text)
        return hiragana_to_katakana(hiragana)

    def is_romaji(self, text: str) -> bool:
        return all(ord(c) < 128 for c in text)

    def is_hiragana(self, text: str) -> bool:
        return all('\u3041' <= c <= '\u309f' for c in text if ord(c) > 127)

    def is_katakana(self, text: str) -> bool:
        return all('\u30a1' <= c <= '\u30ff' for c in text if ord(c) > 127)
```

### 2. Dictionary Format Interface

**From jidoujisho (proven):**
```dart
// Base abstraction
abstract class DictionaryFormat {
    Future<DictionarySearchResult> search(String searchTerm);
    Future<List<DictionaryEntry>> getEntries(String term);
}

// Example: Yomichan
class YomichanTermBankFormat implements DictionaryFormat {
    // Load .zip archive, parse JSON
    // Index for fast search
}
```

**Python equivalent:**
```python
from abc import ABC, abstractmethod
from typing import Optional

class DictionaryEntry:
    def __init__(self, word: str, reading: Optional[str], definition: str):
        self.word = word
        self.reading = reading
        self.definition = definition

class DictionaryFormat(ABC):
    """Base for pluggable dictionary loaders."""

    @abstractmethod
    async def load(self, archive_path: str) -> None:
        """Load dictionary from file."""
        pass

    @abstractmethod
    async def search(self, term: str) -> list[DictionaryEntry]:
        """Search dictionary for term."""
        pass

    @abstractmethod
    async def get_by_reading(self, reading: str) -> list[DictionaryEntry]:
        """Search by reading (hiragana/katakana)."""
        pass

class YomichanFormat(DictionaryFormat):
    """Yomichan JSON archive format (used by jidoujisho)."""

    async def load(self, archive_path: str) -> None:
        """Load Yomichan .zip archive."""
        import zipfile
        import json

        with zipfile.ZipFile(archive_path) as zf:
            # Load term_bank_*.json files
            # Build in-memory index for O(1) lookup
            pass

    async def search(self, term: str) -> list[DictionaryEntry]:
        """Fast O(1) lookup from in-memory index."""
        # Return matching entries
        pass
```

---

## Part 9: Recommended Priority Implementation

### Tier 1: CRITICAL (Do First)

1. **Fix NLP Tokenizer** - Current fallback is broken
   - Adds proper romanji mapping (use pykakasi)
   - Implements multi-level fallback chain
   - Estimated: 1-2 weeks
   - Impact: Dictionary lookups will actually work

2. **Create Language Abstraction** - Required for multi-lang support
   - Estimated: 1 week
   - Impact: Foundation for scaling beyond Japanese

### Tier 2: HIGH (Do Second)

3. **Create AppState Central Hub** - Adopt jidoujisho's pattern
   - Estimated: 1 week
   - Impact: Plugin system, reduced network calls

4. **DictionaryFormat Abstraction** - Enable Yomichan support
   - Estimated: 2 weeks
   - Impact: User can import own dictionaries (huge UX improvement)

### Tier 3: MEDIUM (Do Third)

5. **Caching Layer** - Redis optimization
   - Estimated: 1 week
   - Impact: 10x faster lookups

6. **User Progress Tracking** - Better history/statistics
   - Estimated: 1-2 weeks
   - Impact: Motivation + learning tracking

### Tier 4: LOW (Polish)

7. **Multi-language Support** - Chinese, Korean
   - Estimated: 3-4 weeks
   - Impact: Wider audience

8. **Offline Support** - PWA + SQLite
   - Estimated: 2-3 weeks
   - Impact: Works without internet

---

## Part 10: Dependencies & Libraries to Adopt

| From Jidoujisho | Purpose | Python Equivalent | Notes |
|-----------------|---------|------------------|-------|
| `kana_kit` | Kana conversions | `pykakasi` | Better than manual mapping |
| `mecab_dart` | Japanese NLP | `sudachi`, `mecab-python3` | Already using sudachi ✅ |
| `ve_dart` | Vietnamese NLP | `pyvi` | If adding Vietnamese |
| `objectbox` | Local database | SQLAlchemy + SQLite | For offline support |
| `kanjium` | Pitch accents | JPMDICT data | Import as JSON/SQLite |
| `flutter_archive` | ZIP parsing | `zipfile` (stdlib) | For Yomichan import |
| `subtitle` | Subtitle parsing | `pysubs2` | Future: video features |

---

## Part 11: Testing Strategy

### Unit Tests (By Priority)

1. **NLP Tests**
   ```python
   def test_fallback_terms():
       jp = JapaneseSudachi()
       # "いった" → ["いった", "いく", "イク", ...]
       terms = jp.get_fallback_terms("いった")
       assert "いく" in terms
   ```

2. **Dictionary Tests**
   ```python
   def test_yomichan_search():
       yomichan = YomichanFormat()
       await yomichan.load("jmdict.zip")
       results = await yomichan.search("こんにちは")
       assert len(results) > 0
   ```

3. **Language Abstraction Tests**
   ```python
   def test_language_get_word_info():
       lang = JapaneseSudachi()
       lang.dictionaries = [YomichanFormat()]
       info = await lang.get_word_info("いった")
       assert info.definition != "Not found"
   ```

### Integration Tests

1. End-to-end word lookup flow
2. Multi-language routing
3. Cache hit/miss scenarios
4. Offline fallback mode

---

## Part 12: Deployment Considerations

### For Production (Adopting Jidoujisho's Lessons)

1. **Offline-First Mindset**
   - Don't assume internet always available
   - Cache aggressively
   - Fallback gracefully

2. **Dictionary Pre-Loading**
   - Load at startup, not on-demand
   - Use indexing (B-tree, trie) for O(log n) search
   - Pre-warm cache with top 10K words

3. **Monitoring & Telemetry**
   - Track lookup success rate
   - Monitor cache hit ratio
   - Alert on tokenizer errors

4. **Data Import/Export**
   - Support Yomichan format (proven by jidoujisho)
   - Export user data regularly
   - Allow history/dictionary backup

---

## Conclusion

JapaLearn has solid modern infrastructure (FastAPI, React, Docker) but needs **foundational improvements** in NLP, dictionary system, and state management to match jidoujisho's production maturity.

**Recommended Approach:**
1. Copy proven patterns from jidoujisho (Language, DictionaryFormat abstractions)
2. Improve tokenizer with multi-level fallbacks
3. Build AppState hub for plugin system
4. Add caching layer for performance
5. Implement multi-language support
6. Test thoroughly against jidoujisho's capabilities

**Estimated Timeline:** 10-12 weeks to feature parity + production readiness

**Key Risk:** If jidoujisho patterns not adopted, JapaLearn will eventually hit same limitations (poor NLP, hardcoded languages, network dependency).
