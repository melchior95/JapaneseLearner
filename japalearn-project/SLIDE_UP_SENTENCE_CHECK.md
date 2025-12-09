# Slide-Up Sentence Check Feature

## Overview

The slide-up sentence check feature allows users to get instant AI feedback on their Japanese sentences before continuing the conversation. When practicing in Japanese mode, users can slide up while recording to have ChatGPT check their sentence for grammar errors, suggest corrections, and provide encouragement.

## User Experience

### How It Works

1. **Select Japanese Mode**: Switch to 日本語 (Japanese) mode using the language toggle
2. **Hold to Record**: Press and hold the microphone button to start recording your Japanese sentence
3. **Choose Your Action**:
   - **Slide Left (←)**: Cancel the recording
   - **Slide Up (↑)**: Check your sentence for errors (only in Japanese mode)
   - **Release**: Send normally and continue conversation

### Visual Feedback

When recording in Japanese mode, the interface shows two gesture indicators:

- **Left Side**: Red X icon - Slide left to cancel
- **Right Side**: Green checkmark icon - Slide up to check sentence

As you slide:
- The corresponding icon highlights and grows larger
- The microphone button changes color:
  - Blue = Recording normally
  - Red = Canceling
  - Green = Checking sentence
- Status text updates to show which action will occur on release

### AI Response Modes

#### If Sentence is Correct

ChatGPT responds with:
- **Confirmation**: "素晴らしい！" (Excellent!)
- **Repetition**: "「[your sentence]」と言いましたね。" (You said "[your sentence]".)
- **Positive Feedback**: Brief encouragement in Japanese
- **Continuation**: Naturally continues the conversation in the scenario context

**Example**:
```
User: コーヒーを一つください
AI: 素晴らしい！「コーヒーを一つください」と言いましたね。
    とても丁寧です！サイズはいかがですか？
```

#### If Sentence Has Errors

ChatGPT responds with:
- **Gentle Correction**: Points out the error in Japanese
- **Corrected Version**: "正しくは「[correct sentence]」と言います。" (The correct way is "[correct sentence]".)
- **Brief Explanation**: What was wrong and why
- **Encouragement**: Asks to try again or continue the conversation

**Example**:
```
User: コーヒーが一つください (incorrect particle)
AI: いい試みです！でも、少し直しましょう。
    正しくは「コーヒーを一つください」と言います。
    「を」は目的語を示す助詞です。もう一度言ってみてください。
```

### User Can Then:

1. **Shadow the Correction**: Click the TTS button to hear proper pronunciation
2. **Try Again**: Record the corrected sentence
3. **Continue Conversation**: Move forward with the dialogue
4. **Click Words**: Tap any word for detailed dictionary information
5. **Long-Press**: Hold on the correction for deeper grammar explanation

## Technical Implementation

### Frontend Changes

#### VoiceRecorder Component (`VoiceRecorder.tsx`)

**New Props**:
```typescript
interface VoiceRecorderProps {
  onSend: (audioBlob: Blob) => void;
  onCheckSentence?: (audioBlob: Blob) => void;  // New prop
  onCancel?: () => void;
  language: 'en' | 'ja';
}
```

**New State**:
```typescript
const [isCheckMode, setIsCheckMode] = useState(false);
const [slideOffsetX, setSlideOffsetX] = useState(0);
const [slideOffsetY, setSlideOffsetY] = useState(0);  // Track vertical slide
const startYRef = useRef<number>(0);  // Track starting Y position
```

**Gesture Detection Logic**:
```typescript
const handlePointerMove = (e: React.PointerEvent) => {
  const diffX = startXRef.current - e.clientX; // Positive = left
  const diffY = startYRef.current - e.clientY; // Positive = up
  const threshold = 100; // pixels

  // Determine dominant direction
  if (diffX > 0 && Math.abs(diffX) > Math.abs(diffY)) {
    // Slide left - cancel mode
    if (diffX >= threshold) setIsCancelled(true);
  } else if (diffY > 0 && Math.abs(diffY) > Math.abs(diffX)) {
    // Slide up - check mode
    if (diffY >= threshold) setIsCheckMode(true);
  }
};
```

**Release Handler**:
```typescript
const handlePointerUp = () => {
  if (isCancelled) {
    cancelRecording();
  } else if (isCheckMode) {
    stopRecording(true); // Pass true for check mode
  } else {
    stopRecording(false); // Normal send
  }
};
```

**Visual Indicators**:
- Two-icon layout showing both cancel and check options
- Only shows check option when `language === 'ja'` and `onCheckSentence` is provided
- Icons animate and change color based on gesture state
- Button transforms in both X and Y directions: `translate(-${slideOffsetX}px, -${slideOffsetY}px)`

#### ConversationPage (`ConversationPage.tsx`)

**New Handler**:
```typescript
const handleCheckSentence = async (audioBlob: Blob) => {
  // Transcribe audio
  const recognizeResult = await recognizeSpeech(audioFile, language);
  const transcribedText = recognizeResult.text;

  // Add user message
  setMessages((prev) => [...prev, userMessage]);

  // Send with check_sentence flag
  sendMessageMutation.mutate({
    conversation_id: conversationId,
    message: transcribedText,
    language,
    check_sentence: true,  // ← Key difference
  });
};
```

**VoiceRecorder Integration**:
```typescript
<VoiceRecorder
  onSend={handleVoiceMessage}
  onCheckSentence={language === 'ja' ? handleCheckSentence : undefined}
  language={language}
/>
```

**Updated Info Banner**:
- Conditionally shows "Slide up to check your sentence" only in Japanese mode
- Explains the sentence checking feature

### Backend Changes

#### API Request Model (`conversation.py`)

**Updated MessageRequest**:
```python
class MessageRequest(BaseModel):
    conversation_id: str
    message: str
    language: str  # 'en' or 'ja'
    check_sentence: bool = False  # New parameter
```

#### Endpoint Logic

**Conditional System Prompt**:
```python
if request.check_sentence:
    system_prompt = """You are a Japanese language teacher checking a student's sentence.

Analyze the sentence they just said in Japanese. If it's correct:
- Start with "素晴らしい！" (Excellent!)
- Repeat what they said: "「[their sentence]」と言いましたね。"
- Give brief positive feedback in Japanese
- Then naturally continue the conversation in the scenario context

If there are errors:
- Gently point out the error in Japanese
- Provide the corrected version: "正しくは「[correct sentence]」と言います。"
- Explain briefly what was wrong
- Ask them to try again or continue the conversation

Keep it encouraging and conversational. Respond entirely in Japanese."""
else:
    # Normal conversation system prompt
    system_prompt = """You are a helpful conversation partner..."""
```

**Response Processing**:
- Same tokenization and TTS generation
- Same message storage
- Different AI behavior based on check_sentence flag

### API Client (`client.ts`)

**Updated Function Signature**:
```typescript
export const sendConversationMessage = async (data: {
  conversation_id: string;
  message: string;
  language: 'en' | 'ja';
  check_sentence?: boolean;  // New parameter
  audio_url?: string;
}) => {
  const response = await api.post('/api/v1/conversation/message', data);
  return response.data;
};
```

## User Benefits

### Learning Advantages

1. **Immediate Feedback**: Get corrections before committing to incorrect patterns
2. **Confidence Building**: Know when you're using Japanese correctly
3. **Grammar Understanding**: Receive explanations for errors
4. **Natural Flow**: Corrections are conversational, not academic
5. **Shadow Practice**: Can immediately practice the corrected version
6. **Contextual Learning**: Errors corrected within the scenario context

### UX Advantages

1. **Non-Intrusive**: Check only when uncertain
2. **Fast Gesture**: Simple upward slide motion
3. **Visual Clarity**: Clear indicators showing available actions
4. **Smooth Integration**: Works seamlessly with existing conversation flow
5. **Language-Specific**: Only appears in Japanese mode

## Usage Scenarios

### Scenario 1: Beginner Learner
```
User is practicing café ordering but unsure about particles:
1. Records: "コーヒーが一つください"
2. Slides up (uncertain about particle)
3. AI responds: "正しくは「コーヒーを一つください」..."
4. User clicks TTS to hear correct version
5. Records again with correct particle
6. Conversation continues
```

### Scenario 2: Intermediate Practice
```
User attempting complex sentence:
1. Records: "昨日、映画を見に行きたかったです"
2. Slides up to verify tense/form
3. AI responds: "素晴らしい！完璧です！..."
4. User gains confidence
5. Continues conversation naturally
```

### Scenario 3: Quick Check
```
User made a typo or mispronounced:
1. Records sentence, realizes mistake mid-sentence
2. Continues to end of thought
3. Slides up instead of sending
4. Gets correction and explanation
5. Re-records correctly
```

## Gesture Threshold Details

**Slide Distance**: 100 pixels in any direction
**Priority**: Whichever direction (X or Y) has greater absolute value wins
**Visual Feedback**: Gradual highlighting starts at 50px

```typescript
if (Math.abs(diffX) > Math.abs(diffY)) {
  // Horizontal movement wins
} else if (Math.abs(diffY) > Math.abs(diffX)) {
  // Vertical movement wins
}
```

## Design Decisions

### Why Slide Up?

1. **Natural Gesture**: Up = "check", "verify", "look at"
2. **Distinct from Cancel**: Left is already used for cancel
3. **Easy to Execute**: Thumb naturally moves up while holding
4. **Visual Metaphor**: Upward = raising hand to ask question

### Why Japanese Mode Only?

- English speakers aren't practicing Japanese grammar
- English messages are already translated, showing correct Japanese
- Reduces cognitive load in English mode
- Keeps interface simpler when not needed

### Why Not a Separate Button?

- Gestures are faster than button taps
- Maintains flow of voice recording
- Reduces UI clutter
- Consistent with WhatsApp-style slide-to-cancel pattern

## Accessibility

**Alternative for Non-Touch Devices**:
- Future: Keyboard shortcut (e.g., Shift+Enter for check mode)
- Mouse users can still drag in Y direction

**Visual Indicators**:
- Large icons (8x8) for visibility
- Color coding (red=cancel, green=check, blue=normal)
- Text labels in addition to icons
- High contrast in dark mode

## Testing Checklist

- [ ] Slide left 100px triggers cancel mode
- [ ] Slide up 100px triggers check mode
- [ ] Release after slide left cancels recording
- [ ] Release after slide up sends with check_sentence=true
- [ ] Normal release sends without checking
- [ ] Check indicator only shows in Japanese mode
- [ ] GPT responds with "素晴らしい" for correct sentences
- [ ] GPT provides corrections for incorrect sentences
- [ ] Corrected sentences are tokenized properly
- [ ] TTS works on correction messages
- [ ] Visual feedback matches gesture state
- [ ] Button color changes (blue/red/green)
- [ ] Icons highlight at 50px threshold
- [ ] Diagonal slides prefer dominant direction

## Future Enhancements

1. **Severity Levels**: Minor vs major error indicators
2. **Progress Tracking**: Track accuracy over time
3. **Common Mistakes**: Learn user's frequent errors
4. **Confidence Score**: Show AI's confidence in correction
5. **Alternative Phrasings**: Suggest multiple correct ways
6. **Pronunciation Check**: Audio analysis for accent
7. **Writing Mode**: Type instead of voice, still check
8. **Explanation Depth**: Quick check vs detailed analysis
9. **Custom Sensitivity**: Adjust how strict the checking is
10. **Error Categories**: Grammar, particle, politeness level, etc.

## Conclusion

The slide-up sentence check feature provides learners with instant, contextual feedback on their Japanese sentences. By integrating seamlessly into the conversation flow through a natural gesture, it empowers users to learn with confidence while maintaining the naturalness of conversation practice.

The feature leverages GPT-4's language understanding to provide encouraging, conversational corrections that help learners improve without disrupting their practice flow. Combined with existing features like clickable words, TTS playback, and long-press explanations, it creates a comprehensive learning environment within the conversation practice interface.
