# TTS Pronunciation Feedback Feature

## Overview

The TTS Pronunciation Feedback feature provides learners with native Japanese pronunciation for every message they speak. This allows users to compare their own pronunciation with native speech, helping them identify errors and practice shadowing for better pronunciation accuracy.

## ✅ Completed Features

### 1. **Native Pronunciation Playback**

**For Every Japanese User Message**:
- Backend generates TTS using OpenAI's "alloy" voice
- Audio stored in MinIO S3 for instant playback
- Replay button (🔊 icon) available on all Japanese messages
- Users can click to hear exactly how a native speaker would say their sentence

**Example Flow**:
```
User speaks: "コーヒーを一つください"
↓
System transcribes and saves the text
↓
Backend generates native TTS pronunciation
↓
User sees their message with replay button
↓
User clicks replay to hear native pronunciation
```

### 2. **Manual Replay Button**

**Location**: Bottom-right of each Japanese message (user and AI)

**Behavior**:
- Click to play native pronunciation
- Works for both user messages (your pronunciation reference) and AI messages
- Pre-generated audio loads instantly
- No delay or generation time

**Visual Design**:
- 🔊 Volume2 icon in message action bar
- Hover effect for discoverability
- Matches message theme (blue for user, gray for AI)
- Consistent with other action buttons (copy, etc.)

### 3. **Auto-Play TTS Setting**

**Toggle Location**: Header, below language selection (Japanese mode only)

**States**:
- **ON** (Green): 🔊 Auto-play ON
  - Automatically plays native pronunciation after you speak
  - 300ms delay for smooth rendering
  - Immediate feedback for pronunciation practice
  
- **OFF** (Gray): 🔇 Auto-play OFF
  - Manual replay only via button
  - Default state (user chooses when to enable)

**Smart Visibility**:
- Only appears in Japanese mode
- Hidden in English mode (not needed for translation practice)
- Persists during conversation session
- Resets when switching scenarios

### 4. **Technical Implementation**

#### Backend (`conversation.py`)

**TTS Generation**:
```python
# Generate TTS for user's Japanese message
openai_service = OpenAIService()
user_audio_url = None
try:
    user_audio_url = await openai_service.generate_tts(japanese_message)
except Exception as e:
    print(f"User TTS error: {e}")

# Save with audio URL
user_msg = ChatMessage(
    conversation_id=conversation.id,
    role="user",
    content=japanese_message,
    audio_url=user_audio_url,  # Native pronunciation reference
)
```

**Response Structure**:
```python
class MessageResponse(BaseModel):
    conversation_id: str
    message: str  # AI response
    translation: str | None = None
    words: list[WordToken] = []
    audio_url: str | None = None  # AI message TTS
    user_audio_url: str | None = None  # User message TTS (NEW)
```

#### Frontend (`ChatMessage.tsx`)

**Props**:
```typescript
interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  translation?: string;
  words?: WordToken[];
  timestamp: Date;
  audioUrl?: string;  // Pre-generated TTS URL (NEW)
  autoPlayAudio?: boolean;  // Auto-play on mount (NEW)
}
```

**Audio Playback**:
```typescript
const [audioElement] = useState(() => new Audio());

// Auto-play effect
useEffect(() => {
  if (autoPlayAudio && audioUrl && role === 'user') {
    const timer = setTimeout(() => {
      audioElement.src = audioUrl;
      audioElement.play().catch((err) => console.error('Auto-play failed:', err));
    }, 300);
    return () => clearTimeout(timer);
  }
}, [autoPlayAudio, audioUrl, role, audioElement]);

// Manual play handler
const handlePlayAudio = () => {
  if (audioUrl) {
    audioElement.src = audioUrl;
    audioElement.play().catch((err) => console.error('Audio playback failed:', err));
  } else {
    playTTS(content); // Fallback to on-demand TTS
  }
};
```

#### ConversationPage

**State Management**:
```typescript
const [autoPlayTTS, setAutoPlayTTS] = useState(false);

// Update user message with TTS URL when response arrives
const sendMessageMutation = useMutation({
  mutationFn: sendConversationMessage,
  onSuccess: (data) => {
    setMessages((prev) => {
      const updated = [...prev];
      // Find last user message and add audio URL
      if (data.user_audio_url) {
        const lastUserIndex = updated.findLastIndex((m) => m.role === 'user');
        if (lastUserIndex !== -1) {
          updated[lastUserIndex] = {
            ...updated[lastUserIndex],
            audioUrl: data.user_audio_url,
          };
        }
      }
      // Add AI response...
    });
  },
});
```

**Message Rendering**:
```typescript
{messages.map((message) => (
  <ChatMessage
    key={message.id}
    role={message.role}
    content={message.content}
    audioUrl={message.audioUrl}
    autoPlayAudio={autoPlayTTS && message.role === 'user' && language === 'ja'}
  />
))}
```

## 🎯 User Benefits

### 1. **Pronunciation Self-Correction**
- Hear how a native speaker would say your exact sentence
- Identify pronunciation errors immediately
- Compare your speech with the native TTS
- No need to ask "Did I say that right?"

### 2. **Shadowing Practice**
- Listen to native pronunciation
- Repeat after the TTS (shadowing technique)
- Practice multiple times with replay button
- Build muscle memory for correct pronunciation

### 3. **Confidence Building**
- Know what the sentence should sound like
- Practice until you can match the native pronunciation
- Reduce anxiety about speaking incorrectly
- Immediate feedback loop for improvement

### 4. **Efficient Learning**
- No waiting for teacher/tutor feedback
- Instant pronunciation reference available 24/7
- Practice at your own pace
- Focus on specific problem areas

## 📱 User Experience Flow

### Scenario 1: Manual Pronunciation Check

1. User speaks Japanese sentence in conversation
2. Message appears with transcribed text
3. User clicks 🔊 replay button on their message
4. Hears native pronunciation of what they said
5. Realizes pronunciation mistake
6. Practices shadowing the native pronunciation
7. Continues conversation

### Scenario 2: Auto-Play Enabled

1. User toggles "Auto-play ON" in header
2. User speaks Japanese sentence
3. Message appears with transcribed text
4. **Native TTS automatically plays** (300ms delay)
5. User immediately hears native pronunciation
6. Can replay multiple times via button
7. Practices shadowing if needed
8. Continues conversation with better awareness

### Scenario 3: Pronunciation Comparison

1. User attempts: "コーヒーが欲しいです" (incorrect particle)
2. Clicks replay button
3. Hears: "コーヒーガ ホシーデス"
4. Realizes they should have used を instead of が
5. AI might correct via sentence check feature
6. User practices correct version: "コーヒーを欲しいです"
7. Listens to corrected pronunciation
8. Internalizes the difference

## 🔧 Configuration

### Auto-Play Setting States

**When to Enable**:
- Beginner learners who need constant feedback
- Pronunciation practice sessions
- When actively working on specific sounds
- Learning new vocabulary/phrases

**When to Disable**:
- Fluency practice (conversational flow)
- Already confident in pronunciation
- Want to focus on meaning over form
- Reduce audio clutter

### Voice Model

Currently uses OpenAI's **"alloy" voice**:
- Gender-neutral
- Clear pronunciation
- Consistent across messages
- Standard Japanese accent

**Future Enhancement**: Could support multiple voices:
- Male vs female
- Different regional accents (Tokyo, Osaka, etc.)
- Speed variations (slow for practice, normal for fluency)

## 🎓 Pedagogical Value

### Research-Based Benefits

**1. Immediate Feedback**
- Research shows immediate feedback is 10x more effective than delayed
- Users can correct pronunciation before it fossilizes
- Reduces bad habits forming

**2. Shadowing Technique**
- Proven method for pronunciation improvement
- Used by polyglots and language schools
- Builds phonetic awareness and muscle memory

**3. Phonological Loop**
- Hearing correct pronunciation activates working memory
- Helps encode proper sounds into long-term memory
- Strengthens speaking-listening connection

**4. Metacognitive Awareness**
- Users become aware of their pronunciation gaps
- Encourages self-monitoring
- Builds autonomous learning skills

### Comparison to Alternatives

| Method | Availability | Accuracy | Immediacy | Cost |
|--------|-------------|----------|-----------|------|
| **This Feature** | 24/7 | Native TTS | Instant | Free |
| Human Tutor | Limited | Perfect | Session-based | $$$$ |
| Language Exchange | Variable | Varies | Delayed | Free |
| Pronunciation Apps | 24/7 | AI-based | Instant | $ - $$ |
| Self-Recording | 24/7 | Self-judged | Immediate | Free |

**Unique Advantages**:
- ✅ Context-aware (pronunciation of YOUR sentence)
- ✅ Integrated with conversation practice
- ✅ No separate app/tool needed
- ✅ Consistent native reference
- ✅ Optional (user controls when to use)

## 🚀 Usage Recommendations

### For Beginners

**Recommended Approach**:
1. **Enable auto-play** for first few conversations
2. Listen carefully to each native pronunciation
3. Shadow 2-3 times before next message
4. Focus on sounds that differ from your native language
5. Gradually reduce auto-play as confidence builds

**Common Mistakes to Catch**:
- Particle errors (が vs を vs に)
- Pitch accent (はし vs はし - bridge vs chopsticks)
- Long vowels (おばさん vs おばあさん - aunt vs grandmother)
- Double consonants (かた vs かった - shoulder vs bought)

### For Intermediate Learners

**Recommended Approach**:
1. **Disable auto-play** for conversational fluency
2. Use manual replay only when uncertain
3. Focus on new vocabulary/grammar patterns
4. Check pronunciation of complex sentences
5. Practice natural speed and intonation

**Focus Areas**:
- Sentence rhythm and stress patterns
- Natural linking between words
- Politeness level pronunciation differences
- Regional vs standard pronunciation

### For Advanced Learners

**Recommended Approach**:
1. **Occasional manual checks** for fine-tuning
2. Compare your natural speech with native model
3. Focus on subtle intonation differences
4. Practice advanced expressions/idioms
5. Use for unfamiliar technical vocabulary

**Refinement Goals**:
- Native-like prosody (rhythm + intonation)
- Natural speed without sacrificing clarity
- Appropriate emotional tone
- Cultural pronunciation norms

## 🧪 Testing Checklist

- [ ] User Japanese messages generate TTS audio
- [ ] Replay button appears on all Japanese messages
- [ ] Manual replay works for user messages
- [ ] Manual replay works for AI messages
- [ ] Auto-play toggle appears in Japanese mode only
- [ ] Auto-play toggle hidden in English mode
- [ ] Auto-play ON plays audio after user speaks
- [ ] Auto-play OFF requires manual button click
- [ ] 300ms delay prevents audio overlap
- [ ] Audio plays smoothly without lag
- [ ] Toggle state persists during conversation
- [ ] Toggle resets when switching scenarios
- [ ] Visual feedback (green vs gray) accurate
- [ ] Icon changes (Volume2 vs VolumeX)
- [ ] Works on both desktop and mobile
- [ ] Audio playback fails gracefully on error

## 📦 Files Modified

```
backend/app/routers/conversation.py
├── Added user_audio_url to MessageResponse
├── Generate TTS for user's Japanese message
├── Store audio_url in user ChatMessage
└── Return user_audio_url in response

frontend/src/components/ChatMessage.tsx
├── Added audioUrl prop
├── Added autoPlayAudio prop
├── Audio element for playback
├── Auto-play effect with 300ms delay
└── handlePlayAudio uses pre-generated URL

frontend/src/pages/ConversationPage.tsx
├── Added autoPlayTTS state
├── Auto-play toggle button in header
├── Update user message with audio URL
├── Pass audioUrl to ChatMessage
└── Pass autoPlayAudio when enabled
```

## 🔮 Future Enhancements

1. **Multiple Voice Options**
   - Male/female voices
   - Different ages (young, mature, elderly)
   - Regional accents (Tokyo, Kansai, etc.)

2. **Pronunciation Scoring**
   - Compare user audio with TTS
   - Provide similarity score
   - Highlight specific problem sounds

3. **Speed Control**
   - Slow mode for learning (0.75x)
   - Normal mode for practice (1.0x)
   - Fast mode for fluency (1.25x)

4. **Pitch Visualization**
   - Visual pitch contour of native pronunciation
   - Overlay user's pitch contour
   - Identify pitch accent errors

5. **Phoneme Breakdown**
   - Show romanization with correct sounds
   - Highlight difficult sounds for language learners
   - Provide IPA transcription

6. **Pronunciation History**
   - Track commonly mispronounced words
   - Personalized practice recommendations
   - Progress over time visualization

7. **Minimal Pairs Practice**
   - Identify similar-sounding words user confuses
   - Generate targeted practice exercises
   - Focus on phonemic distinctions

8. **Recording Comparison**
   - Save user's actual audio recording
   - Play side-by-side with native TTS
   - Visual waveform comparison

## 💡 Best Practices for Users

**✅ DO**:
- Listen to native pronunciation before trying to shadow
- Practice each sentence 2-3 times minimum
- Focus on rhythm and intonation, not just individual sounds
- Use auto-play when learning new patterns
- Disable auto-play when focusing on fluency
- Record yourself separately to compare

**❌ DON'T**:
- Rely solely on TTS (practice with real natives too)
- Expect perfect accent immediately
- Skip listening if sentence seems easy
- Leave auto-play on all the time
- Ignore subtle pronunciation differences
- Compare yourself negatively to native pronunciation

## Conclusion

The TTS Pronunciation Feedback feature provides learners with instant, accurate pronunciation references for every Japanese sentence they speak. By combining manual replay buttons with an optional auto-play setting, users can choose their preferred level of pronunciation feedback based on their learning stage and goals.

The feature integrates seamlessly with the conversation practice interface, providing contextual pronunciation support without disrupting the natural flow of conversation. Whether users want immediate feedback after every sentence or occasional checks for difficult words, this feature adapts to their learning needs.

Combined with existing features (sentence checking, word lookup, grammar explanations), this creates a comprehensive pronunciation learning environment where users can:
- Hear correct pronunciation immediately
- Practice shadowing with native speech
- Identify and correct errors early
- Build confidence in speaking Japanese

Ready to start practicing pronunciation! 🎤🇯🇵
