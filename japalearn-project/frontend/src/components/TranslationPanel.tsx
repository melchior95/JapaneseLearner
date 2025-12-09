import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { translateText } from '../api/client';
import WordModal from './WordModal';
import ExplanationModal from './ExplanationModal';
import { useVoiceInput } from '../hooks/useVoiceInput';
import { useLongPress } from '../hooks/useLongPress';
import { useTTS } from '../hooks/useTTS';

interface WordToken {
  word: string;
  reading?: string;
  romanji?: string;
  part_of_speech?: string;
  position: number;
}

interface TranslateResponse {
  original: string;
  translated: string;
  romanji?: string;
  source_lang: string;
  target_lang: string;
  words: WordToken[];
}

export default function TranslationPanel() {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<TranslateResponse | null>(null);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const {
    isRecording,
    isProcessing,
    error: voiceError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceInput();

  const { isPlaying: ttsPlaying, play: playTTS } = useTTS();

  const longPressHandlers = useLongPress({
    onLongPress: () => setShowExplanation(true),
    threshold: 500, // 500ms for long press
  });

  const translateMutation = useMutation({
    mutationFn: translateText,
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleTranslate = () => {
    if (!inputText.trim()) return;

    translateMutation.mutate({
      text: inputText,
      source: 'en',
      target: 'ja',
    });
  };

  const handleVoiceInput = async () => {
    if (isRecording) {
      // Stop recording and get transcription
      try {
        const transcription = await stopRecording();
        setInputText(transcription);
      } catch (error) {
        console.error('Voice input error:', error);
      }
    } else {
      // Start recording
      startRecording();
    }
  };

  return (
    <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8">
      {/* Language Selector */}
      <div className="flex items-center justify-center gap-4 mb-6">
        <div className="px-4 py-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
          <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
            English
          </span>
        </div>
        <svg
          className="w-6 h-6 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
          />
        </svg>
        <div className="px-4 py-2 bg-pink-100 dark:bg-pink-900 rounded-lg">
          <span className="text-sm font-medium text-pink-800 dark:text-pink-200">
            日本語 (Japanese)
          </span>
        </div>
      </div>

      {/* Input Area */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Enter English Text
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Type or speak your sentence..."
          className="w-full h-32 px-4 py-3 text-lg border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              handleTranslate();
            }
          }}
        />
        <div className="flex gap-2 mt-2">
          <button
            onClick={handleTranslate}
            disabled={translateMutation.isPending || !inputText.trim()}
            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-xl transition-colors"
          >
            {translateMutation.isPending ? 'Translating...' : 'Translate'}
          </button>
          <button
            onClick={handleVoiceInput}
            disabled={isProcessing}
            className={`px-6 py-3 font-medium rounded-xl transition-colors ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
            }`}
            title={isRecording ? 'Click to stop recording' : 'Click to start voice input'}
          >
            {isProcessing ? '⏳' : isRecording ? '⏹️' : '🎤'}
          </button>
        </div>
        {voiceError && (
          <p className="text-sm text-red-600 dark:text-red-400 mt-2">
            {voiceError}
          </p>
        )}
      </div>

      {/* Translation Result */}
      {result && (
        <div className="space-y-4">
          <div className="p-6 bg-gradient-to-r from-pink-50 to-purple-50 dark:from-pink-900/20 dark:to-purple-900/20 rounded-xl">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Translation
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => playTTS(result.translated)}
                  disabled={ttsPlaying}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Play pronunciation"
                >
                  🔊
                </button>
                <button
                  onClick={() => setShowExplanation(true)}
                  className="p-2 text-purple-500 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-200 hover:bg-purple-100 dark:hover:bg-purple-900/30 rounded-lg transition-colors"
                  title="Get AI explanation"
                >
                  ✨
                </button>
              </div>
            </div>

            {/* Japanese Text - Clickable Words with Long Press */}
            <div
              {...longPressHandlers}
              className="text-3xl font-medium mb-3 text-gray-900 dark:text-white flex flex-wrap gap-1 select-none cursor-pointer p-2 -m-2 rounded-lg hover:bg-gradient-to-r hover:from-purple-100/50 hover:to-pink-100/50 dark:hover:from-purple-900/20 dark:hover:to-pink-900/20 transition-all"
              title="Click words for details • Long-press sentence for AI explanation"
            >
              {result.words.length > 0 ? (
                result.words.map((word, index) => (
                  <span
                    key={index}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedWord(word.word);
                    }}
                    className="cursor-pointer hover:bg-yellow-200 dark:hover:bg-yellow-700 px-1 rounded transition-colors"
                    title={`${word.reading || ''} (${word.romanji || ''})\n${word.part_of_speech || ''}\nClick for details`}
                  >
                    {word.word}
                  </span>
                ))
              ) : (
                <span>{result.translated}</span>
              )}
            </div>

            {/* Romanji */}
            {result.romanji && (
              <p className="text-lg text-gray-600 dark:text-gray-400 italic">
                {result.romanji}
              </p>
            )}
          </div>

          {/* Interactive Tips */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                💡 <strong>Click words</strong> to see detailed explanations and examples
              </p>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
              <p className="text-sm text-purple-800 dark:text-purple-200">
                ✨ <strong>Long-press sentence</strong> or click ✨ for AI grammar explanation with audio
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {translateMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl">
          <p className="text-red-800 dark:text-red-200">
            ❌ Translation failed. Please check your backend connection.
          </p>
        </div>
      )}

      {/* Word Modal */}
      {selectedWord && (
        <WordModal word={selectedWord} onClose={() => setSelectedWord(null)} />
      )}

      {/* AI Explanation Modal */}
      {showExplanation && result && (
        <ExplanationModal
          sentence={result.translated}
          onClose={() => setShowExplanation(false)}
        />
      )}
    </div>
  );
}
