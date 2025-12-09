import { useState, useRef, useCallback } from 'react';
import { generateTTS } from '../api/client';

export function useTTS() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const play = useCallback(async (text: string, voice: string = 'alloy', speed: number = 1.0) => {
    try {
      setError(null);
      setIsLoading(true);

      // Generate TTS audio
      const result = await generateTTS({ text, voice, speed });

      // Create audio element
      const audio = new Audio(result.audio_url);
      audioRef.current = audio;

      // Set up event listeners
      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => {
        setIsPlaying(false);
        setIsLoading(false);
      };
      audio.onerror = () => {
        setError('Failed to play audio');
        setIsPlaying(false);
        setIsLoading(false);
      };

      // Play audio
      await audio.play();
      setIsLoading(false);
    } catch (err) {
      console.error('TTS error:', err);
      setError('Failed to generate audio');
      setIsLoading(false);
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  return {
    isPlaying,
    isLoading,
    error,
    play,
    stop,
  };
}
