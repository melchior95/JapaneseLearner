# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**jidoujisho** is a Flutter-based Android mobile application for language-agnostic immersion learning. It features video playback with interactive subtitle selection, dictionary lookups, image mining via OCR, and Anki card creation and export. The application supports Japanese, Chinese (simplified & traditional), Korean, and English with extensible architecture for new languages, dictionary formats, and media sources.

## Build & Development Commands

All commands assume you're in the `jidoujisho/chisa/` directory:

### Setup
- `flutter pub get` – Install dependencies
- `flutter pub run build_runner build` – Generate ObjectBox database models

### Development & Debugging
- `flutter run` – Run debug build on connected device/emulator
- `flutter analyze` – Run static analysis (linting)
- `flutter pub outdated` – Check for dependency updates
- `flutter pub get --offline` – Use offline packages (if cached)

### Building for Release
- `flutter build apk` – Build APK for Android
- `flutter build appbundle` – Build AAB for Google Play Store
- Generate and manage launcher icons/splash screens (see `pubspec.yaml` for config details)

### Code Generation
- The project uses **ObjectBox** for local database. After modifying `lib/objectbox-model.json`, run:
  ```bash
  flutter pub run build_runner build
  ```

### Testing & Quality
- `dependency_validator` is included in dev dependencies for dependency validation (see `pubspec.yaml`)

## Architecture & Code Organization

### Core Structure
The app uses a **modular plugin-based architecture** where language support, dictionary formats, and media sources are pluggable components:

```
lib/
├── main.dart                    # App initialization with Firebase, permissions, AppModel setup
├── models/
│   └── app_model.dart          # Central ChangeNotifier managing app state, languages, dicts, media sources
├── pages/                       # Main UI screens (Player, Reader, Viewer, Creator, Dictionary)
├── media/                       # Media sourcing abstraction layer
│   ├── media_source.dart        # Abstract base class for all media sources
│   ├── media_type.dart          # Enum for player/reader/viewer/creator
│   ├── media_sources/           # Concrete implementations (YouTube, Local, Browser, TTU Reader, Camera)
│   ├── media_histories/         # SQLite storage for history (media_history.dart, dictionary_media_history.dart)
│   └── media_history_items/     # Data models for history entries
├── dictionary/
│   ├── dictionary_format.dart   # Abstract base for dictionary loaders
│   └── formats/                 # Concrete implementations (Yomichan, CCCEDICT, Naver)
├── language/
│   ├── language.dart            # Abstract base for language support
│   └── languages/               # Concrete implementations (Japanese, Chinese, Korean, English)
├── anki/
│   ├── enhancements/            # Pluggable Anki export extensions (image search, pitch accents, example sentences)
│   └── models/                  # Anki card data structures
└── util/                        # Utilities (AnkiDroid API, OCR, text segmentation, audio)
```

### State Management Pattern
- **Provider pattern**: `AppModel` (lib/models/app_model.dart:50) extends `ChangeNotifier` and is the single source of truth
- All major state flows through `AppModel` which is injected via `ChangeNotifierProvider<AppModel>` in main.dart
- Pages consume state via `Consumer<AppModel>` or `Provider.of<AppModel>`
- The model manages: current language, active dictionaries, media sources, app configuration, audio handler

### Plugin Architecture: Three Key Abstractions

1. **MediaSource** (lib/media/media_source.dart): Base class for sourcing media
   - Subclasses: `PlayerMediaSource` (YouTube, Local, Network), `ReaderMediaSource` (TTU Ebook, Browser), `ViewerMediaSource` (Local images, Camera)
   - Responsibilities: provide UI actions, handle search/navigation, generate thumbnails, manage history
   - **Key pattern**: Each media type (Player/Reader/Viewer/Creator) has its own media source hierarchy

2. **DictionaryFormat** (lib/dictionary/formats/): Abstract loaders for dictionary data
   - Subclasses: YomichanTermBankFormat, CCCEDICTSimplified, NaverDictionaryFormat
   - Used by languages to provide offline dictionary support
   - ObjectBox models store parsed dictionary entries for fast querying

3. **Language** (lib/language/languages/): Pluggable language support
   - Subclasses: JapaneseLanguage, ChineseSimplifiedLanguage, Korean, English
   - Responsibilities: text segmentation, morphological analysis (via MeCab/Ve/Jieba), pitch accent lookup, dictionary format binding
   - Integrates with NLP backends: **MeCab** (Japanese/Korean), **Ve** (Vietnamese), **Jieba** (Chinese)

### Critical Files & Patterns

- **AppModel** (lib/models/app_model.dart): ~1000 LOC hub that registers all plugins and manages app lifecycle
- **Pages** (lib/pages/): UI layers correspond to media types
  - `player_page.dart` (~2000 LOC) – Video/audio with subtitle selection & interactive dictionary
  - `reader_page.dart` – EPUB/HTML reader with sentence mining
  - `viewer_page.dart` (~2000 LOC) – Image/manga viewer with OCR
  - `creator_page.dart` (~1500 LOC) – Card creation and image search
- **Firebase Integration**: Analytics & crash reporting via `firebase_core`, `firebase_analytics`, `firebase_crashlytics`
- **Database**: ObjectBox ORM for local storage (see `lib/objectbox-model.json`)
- **Foreign Language Processing**: Chaquopy integration for Python NLP (jieba for Chinese)

### Design Principles
- **Loose Coupling**: Media sources, dictionaries, and languages are registered at runtime, not compile-time
- **Separation of Concerns**: Text selection logic, dictionary lookup, and export are distinct subsystems
- **Reusable Widgets**: AnkiDroid API integration happens in `util/anki_creator.dart`, not embedded in pages
- **Immutable Models**: Dictionary entries and media history use immutable data classes with ObjectBox annotations

## Important Dependencies & Integrations

- **Flutter 2.x** with Dart >=2.12
- **Provider 6.0+**: State management
- **ObjectBox 1.2+**: Local NoSQL database (replaces SQLite for some data)
- **VLC Player** (`flutter_vlc_player`): Video playback (supports VLC formats)
- **MeCab / Ve / Jieba**: NLP backends for text segmentation
- **Google ML Kit**: OCR for image mining
- **YouTube Explode Dart**: YouTube metadata/stream extraction
- **Flutter InAppWebView**: Browser functionality
- **Chaquopy**: Python runtime on Android (for Jieba)
- **AnkiDroid API**: Export cards directly to AnkiDroid app

## Key Architectural Decisions

1. **Plugin Registry in AppModel**: All media sources, dictionary formats, and languages are instantiated in `AppModel` constructor. Adding support requires modifying `app_model.dart` and registering the new plugin.
2. **Async Media Loading**: Media source implementations use `Future` for network I/O (YouTube, Plex streams). History pagination uses `infinite_scroll_pagination` package.
3. **Subtitle Handling**: External subtitles (SRT/ASS/SSA) are parsed via custom `subtitle` package (Git dependency). Embedded subtitles extracted via `flutter_ffmpeg`.
4. **Pitch Accent Data**: Japanese pitch accents loaded from bundled `assets/kanjium/accents.txt` at runtime.
5. **Multi-language UI**: Localization via `language/app_localizations.dart` with runtime locale switching (no build-time code gen).

## Common Development Tasks

### Adding a New Dictionary Format
1. Create class extending `DictionaryFormat` in `lib/dictionary/formats/`
2. Implement abstract methods: dictionary loading, entry lookup
3. Register in `AppModel.initialiseAppModel()` in the appropriate language's dictionary list
4. Add UI for user selection (if needed)

### Adding a New Media Source
1. Create class extending appropriate `*MediaSource` base (e.g., `PlayerMediaSource`)
2. Implement required methods: search, history thumbnail, UI actions
3. Register in `AppModel.initialiseAppModel()`
4. Media source will auto-appear in the source picker UI for its media type

### Adding Language Support
1. Create class extending `Language` in `lib/language/languages/`
2. Implement text segmentation (via MeCab/Ve/Jieba depending on language)
3. Optionally bind dictionary formats
4. Register in `AppModel.initialiseAppModel()`
5. Add localization strings in `app_localizations.dart`

## Development Notes

- **Scoped Storage**: Android 10+ (API 30+) requires `MANAGE_EXTERNAL_STORAGE` permission (handled in main.dart)
- **H.265 Support**: VLC player handles H.265 codec; app targets API 29+ for broader compatibility
- **ObjectBox Generation**: After schema changes, run `flutter pub run build_runner build` (takes ~10s)
- **Large Page Files**: Some pages (player_page.dart, viewer_page.dart) exceed 2000 LOC; refactoring into smaller widgets is ongoing
- **Firebase**: Requires valid `google-services.json` (Android) and GoogleService-Info.plist (iOS) for builds

## Linting & Code Style

- Standard Flutter linting rules from `flutter_lints` package (see `analysis_options.yaml`)
- Run `flutter analyze` to check for issues
- No custom lint rules; adheres to Dart code style conventions
