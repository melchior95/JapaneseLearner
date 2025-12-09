# JapaLearn - Japanese Learning Tool

An AI-powered Japanese language learning application inspired by Google Translate, with advanced features for grammar analysis, word explanations, and interactive learning.

## Features

### Phase 1 (Core Features)
- ✅ **Text/Voice Translation**: Translate English to Japanese using text or voice input
- ✅ **Word Analysis**: Click any Japanese word for detailed explanations
  - Kanji breakdown
  - Reading (hiragana/romanji)
  - Part of speech
  - JLPT level
  - Example sentences
- ✅ **AI Explanations**: Long-press any sentence for comprehensive grammar breakdown
- ✅ **Text-to-Speech**: Listen to pronunciation with adjustable speed
- ✅ **Voice Q&A**: Ask grammar questions using voice or text
- ✅ **Learning History**: Track your progress and favorite words

### Phase 2 (Advanced Features)
- 📸 **OCR for Manga/Images**: Upload images and detect Japanese text
- 🎥 **Video Overlay**: Real-time subtitle translation for videos
- 📱 **Mobile App**: iOS and Android support (or PWA)
- 📚 **Spaced Repetition**: Smart review system for vocabulary

## Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand
- **API**: TanStack Query (React Query)
- **Audio**: Web Audio API

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Storage**: MinIO (S3-compatible)
- **Authentication**: JWT

### AI Services
- **Translation**: Google Cloud Translate API
- **STT**: OpenAI Whisper (or local faster-whisper)
- **TTS**: OpenAI TTS API
- **AI Explanations**: OpenAI GPT-4
- **Japanese NLP**: sudachipy + spaCy

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Environment Setup

1. Clone the repository and navigate to the project:
```bash
cd JapaLearn
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Add your API keys to `.env`:
```
OPENAI_API_KEY=your_key_here
GOOGLE_TRANSLATE_API_KEY=your_key_here  # Optional, can use free googletrans
```

### Running with Docker (Recommended)

```bash
# Start all services
docker compose up --build

# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Running Locally (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

**Translation**
```bash
POST /api/v1/translate
{
  "text": "I want to order coffee",
  "source": "en",
  "target": "ja"
}
```

**Word Information**
```bash
GET /api/v1/word/{word}/info
```

**AI Explanation**
```bash
POST /api/v1/sentence/explain
{
  "sentence": "コーヒーを注文したいです",
  "detail_level": "comprehensive"
}
```

**Voice Recognition**
```bash
POST /api/v1/voice/recognize
Content-Type: multipart/form-data
```

## Project Structure

```
JapaLearn/
├── backend/              # FastAPI backend service
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── models/       # Database models
│   │   ├── core/         # Config, auth, db
│   │   └── main.py       # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── stores/       # State management
│   │   └── api/          # API client
│   ├── package.json
│   └── Dockerfile
│
├── nginx/                # Reverse proxy config
├── docker-compose.yml
└── .env.example
```

## Development Roadmap

- [x] **Week 1-2**: Project setup and infrastructure
- [ ] **Week 3-4**: Basic translation with clickable words
- [ ] **Week 5**: Voice input integration
- [ ] **Week 6-7**: AI explanations and grammar analysis
- [ ] **Week 8**: Text-to-Speech
- [ ] **Week 9-10**: Voice Q&A chat interface
- [ ] **Week 11**: User authentication and history
- [ ] **Week 12-16**: Phase 2 - OCR and video features
- [ ] **Week 17-20**: Mobile app development

## Contributing

This project is in active development. Contributions are welcome!

## License

MIT License

## Acknowledgments

- Built with inspiration from Google Translate
- Uses JMdict for Japanese dictionary data
- Powered by OpenAI's GPT-4 and Whisper
