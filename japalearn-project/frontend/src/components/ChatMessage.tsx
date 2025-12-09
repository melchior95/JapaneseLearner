import { Volume2, Copy, Check } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useLongPress } from '../hooks/useLongPress';
import { useTTS } from '../hooks/useTTS';
import WordModal from './WordModal';
import ExplanationModal from './ExplanationModal';
import ShadowPractice from './ShadowPractice';

interface WordToken {
  word: string;
  reading?: string;
  romanji?: string;
  part_of_speech?: string;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  translation?: string;
  words?: WordToken[];
  timestamp: Date;
  audioUrl?: string; // Pre-generated TTS audio URL
  onCopy?: () => void;
  autoPlayAudio?: boolean; // Auto-play audio on mount
}

export default function ChatMessage({
  role,
  content,
  translation,
  words,
  timestamp,
  audioUrl,
  onCopy,
  autoPlayAudio = false,
}: ChatMessageProps) {
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [showShadowPractice, setShowShadowPractice] = useState(false);
  const [copied, setCopied] = useState(false);
  const [audioElement] = useState(() => new Audio());

  const { isPlaying, play: playTTS } = useTTS();

  const longPressHandlers = useLongPress({
    onLongPress: () => setShowShadowPractice(true),
    threshold: 500,
  });

  // Auto-play audio on mount if enabled
  useEffect(() => {
    if (autoPlayAudio && audioUrl && role === 'user') {
      // Small delay to ensure smooth rendering
      const timer = setTimeout(() => {
        audioElement.src = audioUrl;
        audioElement.play().catch((err) => console.error('Auto-play failed:', err));
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [autoPlayAudio, audioUrl, role, audioElement]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  };

  const handlePlayAudio = () => {
    if (audioUrl) {
      // Use pre-generated audio URL (for user messages)
      audioElement.src = audioUrl;
      audioElement.play().catch((err) => console.error('Audio playback failed:', err));
    } else {
      // Generate TTS on-the-fly (for AI messages or fallback)
      playTTS(content);
    }
  };

  const isJapanese = words && words.length > 0;

  return (
    <div
      className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-[80%] ${
          role === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
        } rounded-2xl p-4 shadow-sm`}
      >
        {/* Message content */}
        {isJapanese ? (
          <div
            {...longPressHandlers}
            className="mb-2 cursor-pointer"
            title="Click words for details • Long-press for shadow practice"
          >
            <div className="flex flex-wrap gap-1 text-lg">
              {words.map((word, index) => (
                <span
                  key={index}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedWord(word.word);
                  }}
                  className={`hover:bg-yellow-200 dark:hover:bg-yellow-700 px-0.5 rounded cursor-pointer transition-colors ${
                    role === 'user' ? 'text-white' : ''
                  }`}
                  title={`${word.reading || ''} (${word.romanji || ''})\n${
                    word.part_of_speech || ''
                  }`}
                >
                  {word.word}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <p className="mb-2 text-lg">{content}</p>
        )}

        {/* Translation (for user's English messages) */}
        {translation && (
          <div className="mt-3 pt-3 border-t border-blue-400/30">
            <p className="text-sm opacity-90 mb-1">Japanese translation:</p>
            <p className="text-base font-medium">{translation}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200 dark:border-gray-600">
          <span className="text-xs opacity-70">
            {timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>

          <div className="flex items-center gap-2">
            {/* TTS button - only for Japanese messages */}
            {isJapanese && (
              <button
                onClick={handlePlayAudio}
                disabled={isPlaying}
                className={`p-1.5 rounded-lg transition-colors ${
                  role === 'user'
                    ? 'hover:bg-blue-600'
                    : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Replay audio"
              >
                <Volume2 className="w-4 h-4" />
              </button>
            )}

            {/* Copy button */}
            <button
              onClick={handleCopy}
              className={`p-1.5 rounded-lg transition-colors ${
                role === 'user'
                  ? 'hover:bg-blue-600'
                  : 'hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              title="Copy message"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Modals */}
        {selectedWord && (
          <WordModal
            word={selectedWord}
            onClose={() => setSelectedWord(null)}
          />
        )}

        {showExplanation && isJapanese && (
          <ExplanationModal
            sentence={content}
            onClose={() => setShowExplanation(false)}
          />
        )}

        {showShadowPractice && isJapanese && (
          <ShadowPractice
            targetSentence={content}
            audioUrl={audioUrl || ''}
            onClose={() => setShowShadowPractice(false)}
          />
        )}
      </div>
    </div>
  );
}
