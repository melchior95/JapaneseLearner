"""
Script to import Japanese vocabulary into the database.

This script provides sample Japanese words with definitions.
For production, use the full JMdict database.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.db import AsyncSessionLocal, init_db
from app.models.word import JapaneseWord, WordExample


# Sample Japanese vocabulary data
SAMPLE_WORDS = [
    {
        "word": "こんにちは",
        "reading": "こんにちは",
        "romanji": "konnichiwa",
        "part_of_speech": "expression",
        "jlpt_level": 5,
        "frequency_rank": 100,
        "definition_en": "hello; good day; good afternoon",
        "definition_zh": "你好；日安",
        "grammar_notes": {
            "usage": "Common greeting used during daytime",
            "formality": "neutral/polite",
            "context": "Used when meeting someone during the day (roughly 10am-6pm)"
        },
        "examples": [
            {
                "japanese": "こんにちは、元気ですか？",
                "english": "Hello, how are you?",
                "romanji": "Konnichiwa, genki desu ka?",
                "difficulty": 1,
                "context": "casual"
            },
            {
                "japanese": "こんにちは、田中さん。",
                "english": "Hello, Mr. Tanaka.",
                "romanji": "Konnichiwa, Tanaka-san.",
                "difficulty": 1,
                "context": "formal"
            }
        ]
    },
    {
        "word": "コーヒー",
        "reading": "コーヒー",
        "romanji": "kōhī",
        "part_of_speech": "noun",
        "jlpt_level": 5,
        "frequency_rank": 500,
        "definition_en": "coffee",
        "definition_zh": "咖啡",
        "grammar_notes": {
            "origin": "Loanword from English",
            "writing": "Written in katakana for foreign words"
        },
        "kanji_breakdown": None,
        "examples": [
            {
                "japanese": "コーヒーを飲みます。",
                "english": "I drink coffee.",
                "romanji": "Kōhī o nomimasu.",
                "difficulty": 1,
                "context": "casual"
            }
        ]
    },
    {
        "word": "注文",
        "reading": "ちゅうもん",
        "romanji": "chūmon",
        "part_of_speech": "noun",
        "jlpt_level": 4,
        "frequency_rank": 1500,
        "definition_en": "order; request",
        "definition_zh": "订购；点菜",
        "grammar_notes": {
            "usage": "Often used with する to make it a verb: 注文する (to order)",
            "formality": "neutral",
            "common_phrases": ["注文する (to order)", "注文を取る (to take an order)"]
        },
        "kanji_breakdown": {
            "kanji": ["注", "文"],
            "meanings": ["pour; concentrate", "sentence; text"],
            "readings": ["チュウ", "モン"]
        },
        "examples": [
            {
                "japanese": "コーヒーを注文します。",
                "english": "I will order coffee.",
                "romanji": "Kōhī o chūmon shimasu.",
                "difficulty": 2,
                "context": "formal"
            },
            {
                "japanese": "注文してもいいですか？",
                "english": "May I order?",
                "romanji": "Chūmon shite mo ii desu ka?",
                "difficulty": 3,
                "context": "formal"
            }
        ]
    },
    {
        "word": "欲しい",
        "reading": "ほしい",
        "romanji": "hoshii",
        "part_of_speech": "adjective",
        "jlpt_level": 4,
        "frequency_rank": 800,
        "definition_en": "want; desire (for things)",
        "definition_zh": "想要；需要",
        "grammar_notes": {
            "usage": "Used for wanting things/objects, not actions",
            "conjugation": "i-adjective",
            "note": "Use たい (tai) for wanting to do actions"
        },
        "kanji_breakdown": {
            "kanji": ["欲"],
            "meanings": ["desire; want"],
            "readings": ["ヨク", "ほ(しい)"]
        },
        "examples": [
            {
                "japanese": "コーヒーが欲しいです。",
                "english": "I want coffee.",
                "romanji": "Kōhī ga hoshii desu.",
                "difficulty": 2,
                "context": "casual"
            }
        ]
    },
    {
        "word": "を",
        "reading": "を",
        "romanji": "o/wo",
        "part_of_speech": "particle",
        "jlpt_level": 5,
        "frequency_rank": 10,
        "definition_en": "object marker particle",
        "definition_zh": "宾语助词",
        "grammar_notes": {
            "usage": "Marks the direct object of a verb",
            "pronunciation": "Pronounced 'o' despite being written 'wo'",
            "position": "Placed after the direct object, before the verb"
        },
        "examples": [
            {
                "japanese": "本を読みます。",
                "english": "I read a book.",
                "romanji": "Hon o yomimasu.",
                "difficulty": 1,
                "context": "neutral"
            }
        ]
    },
    {
        "word": "です",
        "reading": "です",
        "romanji": "desu",
        "part_of_speech": "auxiliary",
        "jlpt_level": 5,
        "frequency_rank": 5,
        "definition_en": "to be; is (polite copula)",
        "definition_zh": "是（礼貌用语）",
        "grammar_notes": {
            "usage": "Polite form of だ (da)",
            "function": "Copula - links subject and predicate",
            "formality": "polite/formal"
        },
        "examples": [
            {
                "japanese": "これは本です。",
                "english": "This is a book.",
                "romanji": "Kore wa hon desu.",
                "difficulty": 1,
                "context": "formal"
            }
        ]
    },
    {
        "word": "する",
        "reading": "する",
        "romanji": "suru",
        "part_of_speech": "verb",
        "jlpt_level": 5,
        "frequency_rank": 3,
        "definition_en": "to do",
        "definition_zh": "做",
        "grammar_notes": {
            "type": "Irregular verb",
            "usage": "Combined with nouns to create verbs (e.g., 勉強する - to study)",
            "conjugation": "Irregular - must memorize forms"
        },
        "examples": [
            {
                "japanese": "勉強します。",
                "english": "I study.",
                "romanji": "Benkyō shimasu.",
                "difficulty": 1,
                "context": "formal"
            }
        ]
    },
    {
        "word": "が",
        "reading": "が",
        "romanji": "ga",
        "part_of_speech": "particle",
        "jlpt_level": 5,
        "frequency_rank": 8,
        "definition_en": "subject marker particle; but",
        "definition_zh": "主语助词；但是",
        "grammar_notes": {
            "usage": "Marks the subject of a sentence",
            "vs_wa": "が emphasizes the subject, は marks the topic",
            "function": "Also used as conjunction meaning 'but'"
        },
        "examples": [
            {
                "japanese": "私が学生です。",
                "english": "I am a student.",
                "romanji": "Watashi ga gakusei desu.",
                "difficulty": 1,
                "context": "neutral"
            }
        ]
    },
    {
        "word": "学生",
        "reading": "がくせい",
        "romanji": "gakusei",
        "part_of_speech": "noun",
        "jlpt_level": 5,
        "frequency_rank": 600,
        "definition_en": "student",
        "definition_zh": "学生",
        "grammar_notes": {
            "usage": "General term for student at any level",
            "related": "大学生 (daigakusei) = university student"
        },
        "kanji_breakdown": {
            "kanji": ["学", "生"],
            "meanings": ["study; learning", "life; birth"],
            "readings": ["ガク", "セイ"]
        },
        "examples": [
            {
                "japanese": "私は学生です。",
                "english": "I am a student.",
                "romanji": "Watashi wa gakusei desu.",
                "difficulty": 1,
                "context": "formal"
            }
        ]
    },
    {
        "word": "日本語",
        "reading": "にほんご",
        "romanji": "nihongo",
        "part_of_speech": "noun",
        "jlpt_level": 5,
        "frequency_rank": 400,
        "definition_en": "Japanese language",
        "definition_zh": "日语",
        "grammar_notes": {
            "composition": "日本 (Japan) + 語 (language)",
            "usage": "The Japanese language"
        },
        "kanji_breakdown": {
            "kanji": ["日", "本", "語"],
            "meanings": ["sun; day", "origin; book", "language; word"],
            "readings": ["ニ", "ホン", "ゴ"]
        },
        "examples": [
            {
                "japanese": "日本語を勉強します。",
                "english": "I study Japanese.",
                "romanji": "Nihongo o benkyō shimasu.",
                "difficulty": 1,
                "context": "formal"
            }
        ]
    }
]


async def import_words():
    """Import sample Japanese words into database."""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        print(f"Importing {len(SAMPLE_WORDS)} words...")

        for word_data in SAMPLE_WORDS:
            # Check if word already exists
            result = await session.execute(
                select(JapaneseWord).where(JapaneseWord.word == word_data["word"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  - {word_data['word']} already exists, skipping...")
                continue

            # Extract examples
            examples_data = word_data.pop("examples", [])

            # Create word entry
            word = JapaneseWord(**word_data)
            session.add(word)
            await session.flush()

            # Add examples
            for example_data in examples_data:
                example = WordExample(
                    word_id=word.id,
                    japanese_text=example_data["japanese"],
                    english_translation=example_data["english"],
                    romanji=example_data["romanji"],
                    difficulty_level=example_data.get("difficulty", 1),
                    context=example_data.get("context", "neutral")
                )
                session.add(example)

            print(f"  ✓ Added {word_data['word']} ({word_data['romanji']}) with {len(examples_data)} examples")

        await session.commit()
        print("\n✅ Import completed successfully!")
        print(f"Total words imported: {len(SAMPLE_WORDS)}")


async def verify_import():
    """Verify the import was successful."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(JapaneseWord))
        words = result.scalars().all()

        print(f"\n📚 Database now contains {len(words)} words:")
        for word in words:
            print(f"  - {word.word} ({word.romanji}) - {word.definition_en}")


if __name__ == "__main__":
    print("=" * 60)
    print("Japanese Vocabulary Import Script")
    print("=" * 60)
    print()

    asyncio.run(import_words())
    asyncio.run(verify_import())

    print("\n" + "=" * 60)
    print("Done! You can now use these words in the application.")
    print("=" * 60)
