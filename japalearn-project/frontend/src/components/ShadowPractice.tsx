import { useState, useRef } from 'react';
import { Mic, Volume2, CheckCircle, X, RotateCcw } from 'lucide-react';
import { recognizeSpeech, shadowCheck } from '../api/client';

interface WordMatch {
  word: string;
  correct: boolean;
  reading?: string;
  romanji?: string;
}

interface ShadowCheckResult {
  is_perfect: boolean;
  accuracy: number;
  word_matches: WordMatch[];
  message: string;
}

interface ShadowPracticeProps {
  targetSentence: string;
  audioUrl?: string;
  onClose: () => void;
}

export default function ShadowPractice({
  targetSentence,
  audioUrl,
  onClose,
}: ShadowPracticeProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<ShadowCheckResult | null>(null);
  const [successSound] = useState(() => {
    // Success sound (simple beep) - using Web Audio API
    const createSuccessSound = () => {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.frequency.value = 800; // High pitch for success
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + 0.3);
    };
    return { play: createSuccessSound };
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioElementRef = useRef<HTMLAudioElement>(new Audio());

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await processRecording(audioBlob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setResult(null); // Clear previous result
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processRecording = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'shadow-recording.webm', {
        type: audioBlob.type,
      });

      // Transcribe speech
      const recognizeResult = await recognizeSpeech(audioFile, 'ja');
      const spokenSentence = recognizeResult.text;

      // Compare with target
      const checkResult = await shadowCheck({
        target_sentence: targetSentence,
        spoken_sentence: spokenSentence,
      });

      setResult(checkResult);

      // Play success sound if perfect
      if (checkResult.is_perfect) {
        successSound.play();
      }
    } catch (error) {
      console.error('Failed to process recording:', error);
      alert('Failed to check pronunciation. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePlayTarget = () => {
    if (audioUrl) {
      audioElementRef.current.src = audioUrl;
      audioElementRef.current.play().catch((err) => console.error('Audio playback failed:', err));
    }
  };

  const handleRetry = () => {
    setResult(null);
    startRecording();
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              シャドーイング練習
            </h3>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Hold the button and speak the sentence. Release when done.
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Target Sentence */}
          <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-purple-900 dark:text-purple-200">
                Target Sentence:
              </span>
              <button
                onClick={handlePlayTarget}
                disabled={!audioUrl}
                className="flex items-center gap-1 px-3 py-1 rounded-lg bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm disabled:opacity-50"
              >
                <Volume2 className="w-4 h-4" />
                <span>Listen</span>
              </button>
            </div>
            <p className="text-2xl text-gray-900 dark:text-white font-medium">
              {targetSentence}
            </p>
          </div>

          {/* Result Display */}
          {result && (
            <div className="mb-6">
              <div
                className={`p-4 rounded-xl border-2 ${
                  result.is_perfect
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-500'
                    : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  {result.is_perfect ? (
                    <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                  ) : (
                    <RotateCcw className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                  )}
                  <span
                    className={`font-bold text-lg ${
                      result.is_perfect
                        ? 'text-green-900 dark:text-green-200'
                        : 'text-yellow-900 dark:text-yellow-200'
                    }`}
                  >
                    {result.message}
                  </span>
                </div>

                {/* Word-by-word feedback */}
                <div className="flex flex-wrap gap-2 text-xl mb-2">
                  {result.word_matches.map((match, index) => (
                    <span
                      key={index}
                      className={`px-2 py-1 rounded ${
                        match.correct
                          ? 'bg-green-200 dark:bg-green-800 text-green-900 dark:text-green-100'
                          : 'bg-yellow-200 dark:bg-yellow-800 text-yellow-900 dark:text-yellow-100'
                      }`}
                      title={match.correct ? 'Correct!' : 'Try again'}
                    >
                      {match.word}
                    </span>
                  ))}
                </div>

                <div className="text-sm text-gray-700 dark:text-gray-300">
                  Accuracy: {Math.round(result.accuracy * 100)}%
                </div>
              </div>
            </div>
          )}

          {/* Recording Status */}
          {isRecording && (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-center gap-3">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-blue-900 dark:text-blue-200 font-medium">
                  Recording... Release when done
                </span>
              </div>
            </div>
          )}

          {/* Processing Status */}
          {isProcessing && (
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900/20 rounded-xl border border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600" />
                <span className="text-gray-900 dark:text-gray-200 font-medium">
                  Checking pronunciation...
                </span>
              </div>
            </div>
          )}

          {/* Controls */}
          <div className="flex items-center justify-center gap-4">
            {!result && !isRecording && !isProcessing && (
              <button
                onPointerDown={startRecording}
                onPointerUp={stopRecording}
                onPointerCancel={stopRecording}
                className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-2xl font-medium text-lg shadow-lg transition-all active:scale-95"
              >
                <Mic className="w-6 h-6" />
                <span>Hold to Practice</span>
              </button>
            )}

            {result && !isRecording && !isProcessing && (
              <>
                <button
                  onClick={handleRetry}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white rounded-xl font-medium shadow-lg transition-all active:scale-95"
                >
                  <RotateCcw className="w-5 h-5" />
                  <span>Try Again</span>
                </button>

                {result.is_perfect && (
                  <button
                    onClick={onClose}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl font-medium shadow-lg transition-all active:scale-95"
                  >
                    <CheckCircle className="w-5 h-5" />
                    <span>Continue</span>
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
