# JapaLearn - Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key (required for full functionality)
- (Optional) Google Cloud Translate API key

## Getting Started

### 1. Clone or Navigate to Project

```bash
cd /home/user/JapaLearn
```

### 2. Set Up Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required:**
```
OPENAI_API_KEY=sk-your-openai-key-here
```

### 3. Start All Services with Docker Compose

```bash
# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d --build
```

This will start:
- **PostgreSQL** (port 5432) - Database
- **Redis** (port 6379) - Cache
- **MinIO** (ports 9000, 9001) - File storage
- **Backend API** (port 8000) - FastAPI service
- **Frontend** (port 5173) - React app

### 4. Access the Application

Once all services are running:

- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### 5. Test the Translation Feature

1. Open http://localhost:5173 in your browser
2. Type an English sentence (e.g., "I want to order coffee")
3. Click "Translate"
4. Click on any Japanese word to see details (once word database is populated)

## Development Workflow

### Backend Development

```bash
# Run backend locally (without Docker)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL and Redis with Docker
docker compose up postgres redis minio -d

# Run FastAPI with hot reload
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
# Run frontend locally (without Docker)
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v
```

## Common Issues

### Port Already in Use

If you see "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # or :5173, :5432, etc.

# Kill the process or change ports in docker-compose.yml
```

### Database Connection Error

If backend can't connect to database:

```bash
# Check if PostgreSQL is running
docker compose ps

# Restart the database
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Translation Not Working

1. Check that you've added `OPENAI_API_KEY` to `.env`
2. Check backend logs: `docker compose logs backend`
3. Make sure backend is responding: http://localhost:8000/healthz

## Next Steps

### Phase 1A - Basic Translation (Current)

✅ Text input → Japanese translation
🚧 Clickable words (need to populate word database)
⏳ Voice input
⏳ AI explanations
⏳ Text-to-speech

### Populate Word Database

To add Japanese word definitions:

```bash
# Connect to backend container
docker compose exec backend bash

# Run Python script to import JMdict data (to be created)
python scripts/import_jmdict.py
```

### Add More Features

See `README.md` for the full roadmap and feature list.

## API Examples

### Translate Text

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "source": "en", "target": "ja"}'
```

### Get Word Information

```bash
curl http://localhost:8000/api/v1/word/こんにちは/info
```

### Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure123", "username": "learner"}'
```

## Troubleshooting

### Reset Everything

```bash
# Stop all services and remove volumes
docker compose down -v

# Remove all images
docker compose down --rmi all

# Start fresh
docker compose up --build
```

### Check Service Health

```bash
# Backend API
curl http://localhost:8000/healthz

# PostgreSQL
docker compose exec postgres pg_isready -U app

# Redis
docker compose exec redis redis-cli ping
```

## Support

- Documentation: See `README.md`
- Issues: Check backend/frontend logs
- API Docs: http://localhost:8000/docs

Happy Learning! 🎌📚
