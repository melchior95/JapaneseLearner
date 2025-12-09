import { useState, useRef, useEffect } from 'react';
import { Mic, X, CheckCircle } from 'lucide-react';

interface VoiceRecorderProps {
  onSend: (audioBlob: Blob) => void;
  onCheckSentence?: (audioBlob: Blob) => void;
  onCancel?: () => void;
  language: 'en' | 'ja';
}

export default function VoiceRecorder({
  onSend,
  onCheckSentence,
  onCancel,
  language,
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isCancelled, setIsCancelled] = useState(false);
  const [isCheckMode, setIsCheckMode] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [slideOffsetX, setSlideOffsetX] = useState(0);
  const [slideOffsetY, setSlideOffsetY] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startXRef = useRef<number>(0);
  const startYRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Recording timer
  useEffect(() => {
    if (isRecording && !isCancelled && !isCheckMode) {
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setRecordingTime(0);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, isCancelled, isCheckMode]);

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

      mediaRecorder.start();
      setIsRecording(true);
      setIsCancelled(false);
      setIsCheckMode(false);
      setSlideOffsetX(0);
      setSlideOffsetY(0);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = (checkMode: boolean = false) => {
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || mediaRecorder.state === 'inactive') return;

    mediaRecorder.onstop = () => {
      if (!isCancelled) {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        if (checkMode && onCheckSentence) {
          onCheckSentence(audioBlob);
        } else {
          onSend(audioBlob);
        }
      }

      // Stop all tracks
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
      setSlideOffsetX(0);
      setSlideOffsetY(0);
    };

    mediaRecorder.stop();
  };

  const cancelRecording = () => {
    setIsCancelled(true);
    const mediaRecorder = mediaRecorderRef.current;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
    }
    setIsRecording(false);
    setSlideOffsetX(0);
    setSlideOffsetY(0);
    onCancel?.();
  };

  // Mouse/Touch handlers for slide gestures
  const handlePointerDown = (e: React.PointerEvent) => {
    startXRef.current = e.clientX;
    startYRef.current = e.clientY;
    startRecording();
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isRecording) return;

    const diffX = startXRef.current - e.clientX; // Positive = left slide
    const diffY = startYRef.current - e.clientY; // Positive = up slide
    const threshold = 100; // pixels to slide

    // Reset states
    setIsCancelled(false);
    setIsCheckMode(false);

    // Check for slide left (cancel)
    if (diffX > 0 && Math.abs(diffX) > Math.abs(diffY)) {
      setSlideOffsetX(Math.min(diffX, threshold + 20));
      setSlideOffsetY(0);

      if (diffX >= threshold) {
        setIsCancelled(true);
      }
    }
    // Check for slide up (check sentence)
    else if (diffY > 0 && Math.abs(diffY) > Math.abs(diffX)) {
      setSlideOffsetY(Math.min(diffY, threshold + 20));
      setSlideOffsetX(0);

      if (diffY >= threshold) {
        setIsCheckMode(true);
      }
    }
    // Reset if sliding in other directions
    else {
      setSlideOffsetX(0);
      setSlideOffsetY(0);
    }
  };

  const handlePointerUp = () => {
    if (!isRecording) return;

    if (isCancelled) {
      cancelRecording();
    } else if (isCheckMode) {
      stopRecording(true); // Pass true for check mode
    } else {
      stopRecording(false); // Normal send
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="relative">
      {/* Recording overlay */}
      {isRecording && (
        <div className="fixed inset-0 bg-black/50 z-40 flex items-end justify-center pb-20">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 mx-4 max-w-md w-full shadow-2xl">
            {/* Gesture indicators */}
            <div className="flex justify-around mb-4">
              {/* Cancel indicator (left) */}
              <div
                className={`flex flex-col items-center transition-all ${
                  slideOffsetX > 50
                    ? 'opacity-100 scale-110'
                    : 'opacity-40 scale-100'
                }`}
              >
                <X className={`w-8 h-8 mb-1 ${isCancelled ? 'text-red-500' : 'text-gray-400'}`} />
                <p className={`text-xs font-medium ${isCancelled ? 'text-red-500' : 'text-gray-500'}`}>
                  {isCancelled ? 'Release to cancel' : 'Slide ← to cancel'}
                </p>
              </div>

              {/* Check indicator (up) - only show for Japanese mode */}
              {language === 'ja' && onCheckSentence && (
                <div
                  className={`flex flex-col items-center transition-all ${
                    slideOffsetY > 50
                      ? 'opacity-100 scale-110'
                      : 'opacity-40 scale-100'
                  }`}
                >
                  <CheckCircle className={`w-8 h-8 mb-1 ${isCheckMode ? 'text-green-500' : 'text-gray-400'}`} />
                  <p className={`text-xs font-medium ${isCheckMode ? 'text-green-500' : 'text-gray-500'}`}>
                    {isCheckMode ? 'Release to check' : 'Slide ↑ to check'}
                  </p>
                </div>
              )}
            </div>

            {/* Recording indicator */}
            <div className="flex items-center justify-center gap-4 mb-4">
              <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse" />
              <span className="text-2xl font-mono text-gray-900 dark:text-white">
                {formatTime(recordingTime)}
              </span>
            </div>

            {/* Language indicator */}
            <p className="text-center text-gray-600 dark:text-gray-400 mb-2">
              Speaking in: {language === 'en' ? 'English' : '日本語 (Japanese)'}
            </p>

            {/* Status message */}
            {isCancelled && (
              <p className="text-center text-sm text-red-500 font-medium">
                ← Release to cancel recording
              </p>
            )}
            {isCheckMode && (
              <p className="text-center text-sm text-green-500 font-medium">
                ↑ Release to check sentence
              </p>
            )}
            {!isCancelled && !isCheckMode && (
              <p className="text-center text-sm text-gray-500 dark:text-gray-500">
                Release to send
                {language === 'ja' && onCheckSentence && ' • ↑ Slide up to check • '}
                {' • ← Slide left to cancel'}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Voice button */}
      <button
        ref={buttonRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={cancelRecording}
        className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
          isRecording
            ? isCancelled
              ? 'bg-red-500 scale-110'
              : isCheckMode
              ? 'bg-green-500 scale-110 animate-pulse'
              : 'bg-blue-500 scale-110 animate-pulse'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
        style={{
          transform: isRecording
            ? `translate(-${slideOffsetX}px, -${slideOffsetY}px) scale(1.1)`
            : 'scale(1)',
        }}
        title={`Hold to record in ${language === 'en' ? 'English' : 'Japanese'}${language === 'ja' && onCheckSentence ? ' • Slide up to check sentence' : ''}`}
      >
        <Mic className="w-6 h-6 text-white" />
      </button>
    </div>
  );
}
