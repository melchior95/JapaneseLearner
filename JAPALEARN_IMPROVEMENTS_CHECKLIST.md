# JapaLearn Production Readiness Checklist

Based on comparison with battle-tested jidoujisho application.

## 🔴 CRITICAL ISSUES (Fix Before Public Beta)

### 1. NLP Tokenizer Romanji Mapping is Incomplete
- **Problem:** japalearn/tokenizer.py has only ~50 kana mapped; missing dakuten (が,ぎ,etc.)
- **Impact:** Romaji lookups fail for half of Japanese characters
- **Solution:** Use `pykakasi` library instead of hardcoded mapping
- **Effort:** 3-4 hours
- **Files to Change:** `backend/app/services/tokenizer.py`

```python
# BEFORE (Broken)
def _to_romanji(self, hiragana: str) -> str:
    mapping = {"あ": "a", "か": "ka", ...}  # Only 50 chars!
    return "".join(mapping.get(c, c) for c in hiragana)

# AFTER (Fixed)
import pykakasi
kakasi = pykakasi.kakasi()
result = kakasi.convert(text)  # Handles all chars correctly
```

---

### 2. Dictionary Lookup Falls Back to Character Splitting (Useless)
- **Problem:** If exact word not found, returns ["こ", "ん", "に", "ち", "は"] (character array)
- **Impact:** Users see nothing useful when word not in DB
- **Solution:** Implement 6-level fallback chain like jidoujisho
- **Effort:** 1-2 weeks
- **Files to Change:** `backend/app/services/tokenizer.py`, `backend/app/services/jdict_service.py`

```python
# BEFORE (Useless fallback)
def _fallback_tokenize(self, text: str) -> list[dict]:
    return [{"surface": char, "pos": "unknown"} for char in text if char.strip()]

# AFTER (Smart fallback chain)
async def get_fallback_terms(self, word: str) -> list[str]:
    terms = [word]
    terms.append(await self.get_root_form(word))
    terms.append(await self.to_hiragana(word))
    terms.append(await self.to_katakana(word))
    # Strip verb conjugations (た,ている,そうに,etc.)
    # Result: ["いった", "いく", "いく", "イク", ...]
    return terms
```

---

### 3. No Pluggable Language System (Hardcoded Japanese)
- **Problem:** Adding Chinese/Korean requires refactoring entire codebase
- **Impact:** Cannot scale to other languages
- **Solution:** Create `Language` abstract base class (like jidoujisho)
- **Effort:** 1 week
- **Files to Add:** `backend/app/core/language.py`, `backend/app/languages/*.py`

```python
# NEW: Abstract Language class
class Language(ABC):
    @abstractmethod
    async def tokenize(self, text: str) -> list[Token]:
        pass

    @abstractmethod
    async def get_fallback_terms(self, word: str) -> list[str]:
        pass

# NEW: Japanese implementation
class JapaneseLanguage(Language):
    def __init__(self):
        self.sudachi = Dictionary().create()
        self.dictionaries: list[DictionaryFormat] = []

    async def get_word_info(self, word: str) -> WordInfo:
        for term in await self.get_fallback_terms(word):
            for dict_fmt in self.dictionaries:
                result = await dict_fmt.search(term)
                if result:
                    return result
        return WordInfo(word=word, definition="Not found")

# NEW: Use in router
@router.get("/word/{word}/info")
async def get_word_info(word: str, language: str = "ja"):
    lang = app_state.languages[language]
    return await lang.get_word_info(word)
```

---

### 4. No Offline Support (API-Only)
- **Problem:** Every lookup requires PostgreSQL connection; no fallback
- **Impact:** Can't work without internet; doesn't match jidoujisho offline-first design
- **Solution (Phase 2):** Add SQLite cache + PWA
- **Effort:** 2-3 weeks
- **Why Jidoujisho Wins:** Uses ObjectBox for 100% offline functionality

---

## 🟡 HIGH PRIORITY (Before 1.0 Release)

### 5. Create AppState Central Hub
- **Problem:** No plugin registry; duplicated initialization
- **Impact:** Hard to add new languages, dictionaries, services
- **Solution:** Central `AppState` class (like jidoujisho's `AppModel`)
- **Effort:** 1 week
- **Files to Add:** `backend/app/core/app_state.py`

```python
class AppState:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.languages: dict[str, Language] = {}
        self.dictionaries: dict[str, DictionaryFormat] = {}

    async def initialize(self):
        # Load all languages
        self.languages = {
            "ja": await JapaneseLanguage.load(),
            "zh": await ChineseLanguage.load(),  # Future
        }

        # Load dictionaries for each language
        for lang in self.languages.values():
            lang.dictionaries = await self._load_dicts_for_lang(lang)

# Use in all routers via dependency injection
@router.get("/word/{word}/info")
async def get_word_info(word: str, app_state: AppState = Depends(get_app_state)):
    return await app_state.languages["ja"].get_word_info(word)
```

---

### 6. Pluggable Dictionary Formats
- **Problem:** Dictionary data hardcoded to PostgreSQL; can't import user dictionaries
- **Impact:** Can't use Yomichan archives (what jidoujisho uses)
- **Solution:** Create `DictionaryFormat` abstraction
- **Effort:** 2 weeks
- **Files to Add:** `backend/app/dictionary/format.py`, `backend/app/dictionary/yomichan.py`

```python
class DictionaryFormat(ABC):
    @abstractmethod
    async def load(self, archive_path: str) -> None:
        pass

    @abstractmethod
    async def search(self, term: str) -> list[DictionaryEntry]:
        pass

class YomichanFormat(DictionaryFormat):
    async def load(self, archive_path: str):
        # Load .zip, parse JSON, build in-memory index
        pass

    async def search(self, term: str) -> list[DictionaryEntry]:
        # O(1) lookup from index
        pass
```

---

### 7. Fix Frontend State Management
- **Problem:** No persistent user preferences; limited progress tracking
- **Impact:** Users lose settings/history between sessions
- **Solution:** LocalStorage + Server sync (hybrid approach)
- **Effort:** 1 week
- **Files to Change:** `frontend/src/hooks/`, `frontend/src/App.tsx`

```typescript
// Better state management with sync
function useWordHistory() {
    const [history, setHistory] = useLocalStorage('word_history', []);

    // Sync with server (fire-and-forget)
    const syncWithServer = async () => {
        try {
            await fetch('/api/v1/sync/history', { method: 'POST', body: JSON.stringify(history) });
        } catch (e) {
            console.warn('Sync failed, will retry later');
        }
    };

    return { history, setHistory, syncWithServer };
}
```

---

## 🟢 NICE-TO-HAVE (After 1.0)

### 8. Multi-Language Support
- **Timeline:** Weeks 6-8
- **Why Jidoujisho Wins:** Supports 5 languages with same framework
- **Implementation:**
  - Chinese: Use jieba tokenizer + CCCEDICT format
  - Korean: Use MeCab + Naver dictionary

### 9. Pitch Accent Data
- **Timeline:** Week 5
- **Data Source:** Kanjium (same as jidoujisho)
- **Implementation:** Load JSON, store in PostgreSQL

### 10. AnkiDroid Export
- **Timeline:** Week 7-8
- **Why Jidoujisho Wins:** Native API integration for card exports
- **Implementation:** POST to AnkiDroid API with sentence + audio + image

### 11. OCR & Manga Mining
- **Timeline:** Weeks 10-12
- **Why Jidoujisho Wins:** Built-in OCR via Google ML Kit
- **Implementation:** Use EasyOCR + image upload

---

## Implementation Priority Matrix

```
┌─────────────────┬────────────┬──────────┐
│ Feature         │ Effort     │ Impact   │
├─────────────────┼────────────┼──────────┤
│ 1. Fix Romanji  │ 🟢 Short   │ 🔴 HIGH │
│ 2. Fallback     │ 🟢 Short   │ 🔴 HIGH │
│ 3. Language     │ 🟡 Medium  │ 🔴 HIGH │
│ 4. AppState     │ 🟡 Medium  │ 🟡 MED  │
│ 5. DictFormat   │ 🟡 Medium  │ 🟡 MED  │
│ 6. Offline      │ 🔴 Long    │ 🟡 MED  │
│ 7. MultiLang    │ 🔴 Long    │ 🟢 LOW  │
│ 8. PitchAccent  │ 🟢 Short   │ 🟢 LOW  │
│ 9. Anki Export  │ 🟡 Medium  │ 🟢 LOW  │
│ 10. OCR/Manga   │ 🔴 Long    │ 🟢 LOW  │
└─────────────────┴────────────┴──────────┘

Recommended Order:
Week 1-2: #1, #2 (Fix critical bugs)
Week 3:   #3 (Language abstraction)
Week 4-5: #4, #5 (AppState, DictFormat)
Week 6-7: #8, #9 (Polish features)
Week 8-9: #6 (Offline support)
Week 10+: #7, #10 (Nice-to-haves)
```

---

## Testing Checklist

### Unit Tests to Add
- [ ] `test_tokenizer_romanji_mapping()` - All 46 kana + dakuten
- [ ] `test_fallback_terms_generation()` - 6-level chain works
- [ ] `test_language_abstraction()` - Language can be swapped
- [ ] `test_dictionary_format()` - Yomichan loads and searches
- [ ] `test_app_state_initialization()` - All plugins load on startup

### Integration Tests to Add
- [ ] Word lookup end-to-end (no internet)
- [ ] Language switching preserves state
- [ ] User progress tracked correctly
- [ ] Cache hit/miss rates
- [ ] Offline mode fallback

### Performance Tests to Add
- [ ] Tokenizer: < 50ms for 100-char text
- [ ] Dictionary search: < 100ms for 10K+ entries
- [ ] Dictionary load: < 500ms at startup
- [ ] Cache hit rate: > 80% for top 1000 words

---

## Jidoujisho Patterns to Adopt

| Pattern | Location in Jidoujisho | Apply to JapaLearn |
|---------|------------------------|-------------------|
| Language abstraction | `lib/language/language.dart` | Create `Language` ABC |
| Fallback terms | `lib/language/languages/japanese_language.dart:64` | Port to Python |
| Dictionary format | `lib/dictionary/dictionary_format.dart` | Create `DictionaryFormat` ABC |
| Yomichan support | `lib/dictionary/formats/yomichan_term_bank_format.dart` | Create `YomichanFormat` |
| Central AppModel | `lib/models/app_model.dart` | Create `AppState` |
| Plugin registry | `lib/models/app_model.dart:133-140` | Registry in `AppState` |
| ObjectBox caching | `lib/media/media_histories/` | Use Redis + SQLite |

---

## Success Metrics (vs Jidoujisho)

- ✅ Dictionary lookup works for 99% of queries (with fallback chain)
- ✅ Supports 3+ languages (Japanese, Chinese, Korean)
- ✅ Offline mode functional (no internet required)
- ✅ Pluggable architecture (users can add dictionaries)
- ✅ Sub-100ms word lookup (P95)
- ✅ 90%+ cache hit rate for common words
- ✅ Can import Yomichan archives (proven jidoujisho format)
- ✅ User progress tracked across sessions

---

## Resources

- **Jidoujisho Codebase:** `/jidoujisho/chisa/lib/`
- **Documentation:** `INTEGRATION_COMPARISON.md` (detailed guide)
- **Example Implementations:**
  - Japanese: `jidoujisho/chisa/lib/language/languages/japanese_language.dart`
  - Dictionary: `jidoujisho/chisa/lib/dictionary/formats/yomichan_term_bank_format.dart`

---

## Next Steps

1. **Pick #1 (Fix Romanji)** - 4 hours, highest impact
   ```bash
   pip install pykakasi
   # Update tokenizer.py to use pykakasi
   ```

2. **Pick #2 (Fallback Chain)** - 1-2 weeks, reference jidoujisho's fallback generation

3. **Pick #3 (Language Abstraction)** - 1 week, foundation for scaling

4. **Pick #5 (AppState)** - 1 week, enables plugin system

5. **Test thoroughly** - Make sure it works as well as jidoujisho

---

**Total Effort to Match Jidoujisho:** 10-12 weeks
**Recommended Allocation:** 2-3 developers, full-time
**Go-Live Target:** 3 months with this roadmap
