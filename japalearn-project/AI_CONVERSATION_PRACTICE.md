# AI Conversation Practice Feature

## Overview

The AI Conversation Practice feature allows users to engage in realistic Japanese conversation scenarios with GPT-4, using a WhatsApp-style voice recorder interface. This feature combines speech recognition, AI-powered conversations, and interactive learning tools.

## User Experience

### Scenario Selection
Users can choose from 10 pre-built conversation scenarios:
1. 🍵 **Café Ordering** (Beginner) - Order coffee and snacks
2. 🗺️ **Asking for Directions** (Beginner) - Navigate in Japanese cities
3. 🛍️ **Shopping** (Intermediate) - Purchase items at stores
4. 🍜 **Restaurant** (Intermediate) - Order meals and interact with staff
5. 🚆 **Train Station** (Intermediate) - Buy tickets and ask for help
6. 🏨 **Hotel Check-in** (Intermediate) - Check in and request services
7. 🏥 **Doctor's Visit** (Advanced) - Describe symptoms and understand medical advice
8. 💼 **Job Interview** (Advanced) - Professional conversation practice
9. 👥 **Making Friends** (Intermediate) - Casual social interactions
10. 📞 **Phone Conversation** (Advanced) - Handle phone calls in Japanese

Each scenario includes:
- Difficulty level (Beginner/Intermediate/Advanced)
- Custom system prompt for AI behavior
- Starter message to begin the conversation
- Contextual scenario description

### Conversation Interface

#### WhatsApp-Style Voice Recorder
- **Hold to Record**: Press and hold the microphone button to start recording
- **Slide to Cancel**: While holding, slide left 100px to cancel the recording
- **Release to Send**: Release the button to send your message
- **Visual Feedback**:
  - Recording timer displays elapsed time
  - Slide offset indicator shows cancel threshold
  - Language badge (EN/JA) indicates current language

#### Language Toggle
Users can switch between:
- **English Mode**: Messages are transcribed in English, then automatically translated to Japanese for shadowing practice
- **Japanese Mode**: Messages are transcribed directly in Japanese

#### Interactive Messages

**User Messages (English)**:
- Original English text displayed
- Japanese translation shown below for learning
- Copy button to copy text
- Timestamp

**User Messages (Japanese)**:
- Japanese text with clickable words
- Word hover shows reading and romanji
- Click words to see detailed definitions (WordModal)
- Long-press sentence for AI grammar explanation (ExplanationModal)
- TTS button to replay pronunciation
- Copy button

**AI Messages**:
- Japanese text broken down into clickable words
- Each word shows reading, romanji, and part of speech on hover
- Click any word for detailed dictionary information
- Long-press the entire sentence for comprehensive AI grammar explanation
- TTS replay button to hear pronunciation
- Copy button
- Timestamp

## Technical Implementation

### Frontend Components

#### 1. ConversationPage (`/pages/ConversationPage.tsx`)
Main conversation interface with two views:
- **Scenario Selection Grid**: Displays all available scenarios with difficulty badges
- **Conversation Interface**: Chat-style interface with messages and voice recorder

**Key Features**:
- React Query mutations for API calls
- Auto-scroll to latest messages
- Language state management
- Real-time message updates

#### 2. VoiceRecorder (`/components/VoiceRecorder.tsx`)
WhatsApp-style voice recording component.

**Features**:
- Pointer event handling for slide-to-cancel gesture
- Web Audio API for recording
- MediaRecorder for audio capture
- Visual feedback with timer and cancel threshold
- Language indicator badge

**Gesture Detection**:
```typescript
const handlePointerMove = (e: React.PointerEvent) => {
  const diff = startXRef.current - e.clientX;
  const cancelThreshold = 100; // pixels
  if (diff >= cancelThreshold) {
    setIsCancelled(true);
  }
};
```

#### 3. ChatMessage (`/components/ChatMessage.tsx`)
Message display component with interactive features.

**Features**:
- Clickable Japanese words
- Long-press detection (500ms threshold)
- TTS integration
- Copy to clipboard
- WordModal and ExplanationModal integration

#### 4. Scenario Data (`/data/scenarios.ts`)
Defines all conversation scenarios with:
```typescript
interface Scenario {
  id: string;
  title: string;
  titleJa: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  icon: string;
  systemPrompt: string;
  starterMessage: string;
}
```

### Backend API

#### Conversation Router (`/routers/conversation.py`)

**Endpoints**:

1. **POST `/api/v1/conversation/start`**
   - Starts a new conversation with selected scenario
   - Creates ChatConversation record
   - Stores starter message from AI
   - Tokenizes Japanese text for clickable words
   - Generates TTS audio for starter message
   - Returns conversation_id and starter message data

2. **POST `/api/v1/conversation/message`**
   - Accepts user message in English or Japanese
   - If English: translates to Japanese automatically
   - Stores user message in database
   - Sends conversation history (last 10 messages) to GPT-4
   - Receives AI response in Japanese
   - Tokenizes AI response for clickable words
   - Generates TTS audio
   - Stores AI message and returns data

3. **GET `/api/v1/conversation/history/{conversation_id}`**
   - Retrieves full conversation history
   - Returns all messages with tokenization and audio URLs

**Japanese Tokenization**:
Uses sudachipy for accurate word segmentation:
```python
tokenizer_obj = dictionary.Dictionary().create()
tokens = tokenizer_obj.tokenize(text, mode=sudachipy.Tokenizer.SplitMode.C)

for token in tokens:
    word_tokens.append({
        "word": token.surface(),
        "reading": token.reading_form(),
        "romanji": romkan.to_roma(token.reading_form()),
        "part_of_speech": token.part_of_speech()[0]
    })
```

**GPT-4 Integration**:
```python
messages = [
    {"role": "system", "content": system_prompt},
    ...conversation_history,
    {"role": "user", "content": user_message}
]

response = openai_service.chat_completion(
    messages=messages,
    model="gpt-4-turbo-preview"
)
```

### Database Models

**ChatConversation Table**:
- `id`: UUID primary key
- `user_id`: Foreign key to users
- `scenario_id`: Scenario identifier
- `title`: Conversation title
- `description`: Scenario description
- `system_prompt`: AI behavior instructions
- `created_at`, `updated_at`: Timestamps

**ChatMessage Table**:
- `id`: UUID primary key
- `conversation_id`: Foreign key to conversations
- `role`: "user" or "assistant"
- `content`: Message text
- `language`: "en" or "ja"
- `translation`: Translation if applicable
- `audio_url`: S3 URL for TTS audio
- `created_at`: Timestamp

### API Client Functions

**Frontend API Functions** (`/api/client.ts`):
```typescript
// Start new conversation
export const startConversation = async (data: {
  scenario_id: string;
  title: string;
  description: string;
  system_prompt: string;
  starter_message: string;
}) => {
  const response = await api.post('/api/v1/conversation/start', data);
  return response.data;
};

// Send message and get AI response
export const sendConversationMessage = async (data: {
  conversation_id: string;
  content: string;
  language: 'en' | 'ja';
  audio_url?: string;
}) => {
  const response = await api.post('/api/v1/conversation/message', data);
  return response.data;
};

// Get conversation history
export const getConversationHistory = async (conversationId: string) => {
  const response = await api.get(`/api/v1/conversation/history/${conversationId}`);
  return response.data;
};
```

## Features Integration

### 1. Speech Recognition
- Uses OpenAI Whisper API via backend
- Supports both English and Japanese
- Converts WebM audio blob to transcription

### 2. Translation
- Automatic English→Japanese translation for learning
- Displays both languages for shadowing practice
- Uses existing TranslatorService

### 3. Text-to-Speech
- OpenAI TTS with "alloy" voice
- Audio stored in MinIO S3
- Returns public URL for playback
- Available on all AI messages

### 4. Word Lookup
- Clickable Japanese words
- Integration with existing WordModal
- Shows dictionary entries from database
- JLPT level, part of speech, examples

### 5. AI Grammar Explanations
- Long-press detection (500ms)
- GPT-4 powered explanations
- Integration with ExplanationModal
- Grammar breakdown, cultural context, alternatives
- TTS narration of explanations

## User Workflow

1. **Select Scenario**
   - User chooses from 10 conversation scenarios
   - AI sends starter message in Japanese

2. **Toggle Language**
   - User selects English or Japanese input mode
   - Badge displays current language (EN/JA)

3. **Record Message**
   - Hold microphone button to start recording
   - Slide left 100px to cancel (visual feedback)
   - Release to send message

4. **Automatic Processing**
   - Audio transcribed to text (Whisper)
   - If English: auto-translated to Japanese
   - Message sent to GPT-4 with conversation history

5. **AI Response**
   - GPT-4 responds in Japanese (scenario-appropriate)
   - Text tokenized into clickable words
   - TTS audio generated and stored
   - Message displayed with interactive features

6. **Interactive Learning**
   - Click words for dictionary definitions
   - Long-press sentences for grammar explanations
   - Listen to pronunciation with TTS
   - Copy text for practice

7. **Continue Conversation**
   - User responds in English or Japanese
   - Can shadow the provided Japanese sentences
   - Switch languages at any time
   - Natural conversation flow maintained

## Configuration

### Environment Variables

**Backend**:
```bash
OPENAI_API_KEY=your_openai_api_key
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET=japalearn
```

**Frontend**:
```bash
VITE_API_URL=http://localhost:8000
```

### Scenario Customization

Add new scenarios in `/frontend/src/data/scenarios.ts`:
```typescript
{
  id: 'unique-id',
  title: 'English Title',
  titleJa: '日本語タイトル',
  description: 'Detailed description of the scenario',
  difficulty: 'beginner' | 'intermediate' | 'advanced',
  icon: '🎭', // Emoji icon
  systemPrompt: 'You are a [role]. Respond naturally in Japanese...',
  starterMessage: 'こんにちは！', // AI's first message
}
```

## Performance Considerations

1. **Audio Compression**: WebM format for efficient recording
2. **Message Pagination**: Load last 10 messages for GPT-4 context
3. **React Query Caching**: Cached explanations and word lookups
4. **S3 CDN**: Audio files served from MinIO for fast playback
5. **Optimistic Updates**: Messages appear immediately before API confirmation

## Future Enhancements

1. **Conversation History**: Save and review past conversations
2. **Progress Tracking**: Track vocabulary learned and scenarios completed
3. **Voice Variety**: Multiple TTS voices (male/female, regional accents)
4. **Difficulty Adaptation**: AI adjusts complexity based on user level
5. **Vocabulary Flashcards**: Generate flashcards from conversation words
6. **Speaking Assessment**: Pronunciation feedback using speech analysis
7. **Multi-turn Scenarios**: Branching conversation paths
8. **Peer Practice**: Connect users for real conversation practice
9. **Custom Scenarios**: Users create their own conversation scenarios
10. **Offline Mode**: Download scenarios and practice without internet

## Testing

### Manual Testing Checklist

- [ ] Scenario selection displays all 10 scenarios
- [ ] Difficulty badges show correct levels
- [ ] Conversation starts with AI message
- [ ] Language toggle switches between EN/JA
- [ ] Voice recorder hold-to-record works
- [ ] Slide-to-cancel gesture detects 100px threshold
- [ ] Release-to-send uploads and transcribes audio
- [ ] English messages show Japanese translation
- [ ] Japanese words are clickable
- [ ] WordModal displays dictionary information
- [ ] Long-press triggers ExplanationModal
- [ ] TTS playback works for all messages
- [ ] Copy button copies message text
- [ ] Back button returns to scenario selection
- [ ] Messages auto-scroll to bottom
- [ ] AI responses maintain conversation context

### API Testing

```bash
# Start conversation
curl -X POST http://localhost:8000/api/v1/conversation/start \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "cafe",
    "title": "Café Ordering",
    "description": "Practice ordering at a café",
    "system_prompt": "You are a friendly café staff...",
    "starter_message": "いらっしゃいませ！"
  }'

# Send message
curl -X POST http://localhost:8000/api/v1/conversation/message \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "uuid-here",
    "content": "I would like a coffee please",
    "language": "en"
  }'

# Get history
curl http://localhost:8000/api/v1/conversation/history/{conversation_id}
```

## Dependencies

### Frontend
- `react-router-dom`: Navigation and routing
- `lucide-react`: Icon library
- `@tanstack/react-query`: API state management
- Web Audio API: Voice recording
- Pointer Events API: Gesture detection

### Backend
- `sudachipy`: Japanese tokenization
- `romkan`: Romanization conversion
- `openai`: GPT-4 and Whisper integration
- FastAPI: REST API framework
- SQLAlchemy: Database ORM

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatMessage.tsx        # Message display with interactions
│   │   ├── VoiceRecorder.tsx      # WhatsApp-style recorder
│   │   ├── WordModal.tsx          # Word definitions
│   │   └── ExplanationModal.tsx   # AI grammar explanations
│   ├── pages/
│   │   └── ConversationPage.tsx   # Main conversation interface
│   ├── data/
│   │   └── scenarios.ts           # Scenario definitions
│   ├── api/
│   │   └── client.ts              # API functions
│   ├── hooks/
│   │   ├── useLongPress.ts        # Long-press detection
│   │   ├── useVoiceInput.ts       # Voice recording
│   │   └── useTTS.ts              # Text-to-speech
│   └── App.tsx                    # Routing setup

backend/
├── app/
│   ├── routers/
│   │   └── conversation.py        # Conversation API endpoints
│   ├── models/
│   │   └── conversation.py        # Database models
│   └── services/
│       ├── openai_service.py      # OpenAI integration
│       └── translator.py          # Translation service
```

## Success Metrics

1. **User Engagement**: Average conversation length and message count
2. **Learning Effectiveness**: Vocabulary retention and grammar understanding
3. **Feature Usage**: Word clicks, long-press explanations, TTS playback
4. **Language Mix**: Ratio of English vs Japanese messages
5. **Scenario Popularity**: Most frequently chosen scenarios
6. **Completion Rate**: Conversations completed vs abandoned

## Conclusion

The AI Conversation Practice feature provides an immersive, interactive learning experience that combines modern voice interface design (WhatsApp-style) with powerful AI capabilities (GPT-4, Whisper, TTS) and comprehensive learning tools (clickable words, grammar explanations). This creates a natural conversation environment where users can practice Japanese in realistic scenarios while receiving immediate feedback and support.
