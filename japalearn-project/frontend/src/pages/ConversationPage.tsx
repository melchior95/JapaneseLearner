import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ArrowLeft, Globe, MessageCircle, Volume2, VolumeX } from 'lucide-react';
import { scenarios, type Scenario } from '../data/scenarios';
import { startConversation, sendConversationMessage, recognizeSpeech } from '../api/client';
import ChatMessage from '../components/ChatMessage';
import VoiceRecorder from '../components/VoiceRecorder';

interface WordToken {
  word: string;
  reading?: string;
  romanji?: string;
  part_of_speech?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  translation?: string;
  words?: WordToken[];
  timestamp: Date;
  audioUrl?: string;
}

export default function ConversationPage() {
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [language, setLanguage] = useState<'en' | 'ja'>('en');
  const [autoPlayTTS, setAutoPlayTTS] = useState(false); // Auto-play TTS for user messages
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Start conversation mutation
  const startConversationMutation = useMutation({
    mutationFn: startConversation,
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      // Add AI starter message
      setMessages([
        {
          id: data.starter_message_id || '1',
          role: 'assistant',
          content: data.starter_message,
          words: data.starter_words || [],
          timestamp: new Date(),
          audioUrl: data.audio_url,
        },
      ]);
    },
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: sendConversationMessage,
    onSuccess: (data) => {
      setMessages((prev) => {
        // Update the last user message with TTS audio URL
        const updated = [...prev];
        if (data.user_audio_url) {
          const lastUserIndex = updated.findLastIndex((m) => m.role === 'user');
          if (lastUserIndex !== -1) {
            updated[lastUserIndex] = {
              ...updated[lastUserIndex],
              audioUrl: data.user_audio_url,
            };
          }
        }

        // Add AI response to messages
        return [
          ...updated,
          {
            id: data.message_id || `ai-${Date.now()}`,
            role: 'assistant',
            content: data.message,
            words: data.words || [],
            timestamp: new Date(),
            audioUrl: data.audio_url,
          },
        ];
      });
    },
  });

  const handleScenarioSelect = (scenario: Scenario) => {
    setSelectedScenario(scenario);
    startConversationMutation.mutate({
      scenario_id: scenario.id,
      title: scenario.title,
      description: scenario.description,
      system_prompt: scenario.systemPrompt,
      starter_message: scenario.starterMessage,
    });
  };

  const handleBackToScenarios = () => {
    setSelectedScenario(null);
    setConversationId(null);
    setMessages([]);
  };

  const handleVoiceMessage = async (audioBlob: Blob) => {
    if (!conversationId) return;

    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'recording.webm', {
        type: audioBlob.type,
      });

      // Recognize speech
      const recognizeResult = await recognizeSpeech(audioFile, language);
      const transcribedText = recognizeResult.text;

      // Add user message immediately
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: transcribedText,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to backend and get AI response
      sendMessageMutation.mutate({
        conversation_id: conversationId,
        message: transcribedText,
        language,
        check_sentence: false,
      });
    } catch (error) {
      console.error('Failed to process voice message:', error);
      alert('Failed to process voice message. Please try again.');
    }
  };

  const handleCheckSentence = async (audioBlob: Blob) => {
    if (!conversationId) return;

    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'recording.webm', {
        type: audioBlob.type,
      });

      // Recognize speech
      const recognizeResult = await recognizeSpeech(audioFile, language);
      const transcribedText = recognizeResult.text;

      // Add user message immediately
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: transcribedText,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to backend with check_sentence flag
      sendMessageMutation.mutate({
        conversation_id: conversationId,
        message: transcribedText,
        language,
        check_sentence: true, // AI will check the sentence for errors
      });
    } catch (error) {
      console.error('Failed to check sentence:', error);
      alert('Failed to check sentence. Please try again.');
    }
  };

  // If no scenario selected, show scenario selection
  if (!selectedScenario) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <MessageCircle className="w-12 h-12 text-purple-600" />
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                AI Conversation Practice
              </h1>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Choose a scenario and practice real-world Japanese conversations with AI
            </p>
          </div>

          {/* Scenario Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => handleScenarioSelect(scenario)}
                disabled={startConversationMutation.isPending}
                className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed text-left"
              >
                {/* Difficulty Badge */}
                <div className="absolute top-4 right-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      scenario.difficulty === 'beginner'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                        : scenario.difficulty === 'intermediate'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                    }`}
                  >
                    {scenario.difficulty}
                  </span>
                </div>

                {/* Icon */}
                <div className="text-5xl mb-4">{scenario.icon}</div>

                {/* Title */}
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {scenario.title}
                </h3>
                <p className="text-lg text-purple-600 dark:text-purple-400 mb-3">
                  {scenario.titleJa}
                </p>

                {/* Description */}
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                  {scenario.description}
                </p>

                {/* Hover Effect */}
                <div className="mt-4 flex items-center text-purple-600 dark:text-purple-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Start Practice →
                </div>
              </button>
            ))}
          </div>

          {/* Loading State */}
          {startConversationMutation.isPending && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 text-center">
                <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mb-4"></div>
                <p className="text-lg text-gray-900 dark:text-white">
                  Starting conversation...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show conversation interface
  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-lg border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToScenarios}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Back to scenarios"
              >
                <ArrowLeft className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <span>{selectedScenario.icon}</span>
                  {selectedScenario.title}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedScenario.titleJa}
                </p>
              </div>
            </div>

            {/* Settings */}
            <div className="flex flex-col gap-2 items-end">
              {/* Language Toggle */}
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 rounded-xl p-1">
                <button
                  onClick={() => setLanguage('en')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    language === 'en'
                      ? 'bg-white dark:bg-gray-600 shadow-md text-blue-600 dark:text-blue-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  <Globe className="w-4 h-4" />
                  <span className="font-medium">English</span>
                </button>
                <button
                  onClick={() => setLanguage('ja')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    language === 'ja'
                      ? 'bg-white dark:bg-gray-600 shadow-md text-purple-600 dark:text-purple-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  <span className="text-base">🇯🇵</span>
                  <span className="font-medium">日本語</span>
                </button>
              </div>

              {/* Auto-play TTS Toggle */}
              {language === 'ja' && (
                <button
                  onClick={() => setAutoPlayTTS(!autoPlayTTS)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all text-sm ${
                    autoPlayTTS
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  title={
                    autoPlayTTS
                      ? 'Auto-play pronunciation enabled'
                      : 'Auto-play pronunciation disabled'
                  }
                >
                  {autoPlayTTS ? (
                    <>
                      <Volume2 className="w-4 h-4" />
                      <span className="font-medium">Auto-play ON</span>
                    </>
                  ) : (
                    <>
                      <VolumeX className="w-4 h-4" />
                      <span className="font-medium">Auto-play OFF</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
              translation={message.translation}
              words={message.words}
              timestamp={message.timestamp}
              audioUrl={message.audioUrl}
              autoPlayAudio={autoPlayTTS && message.role === 'user' && language === 'ja'}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Voice Recorder Area */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          {/* Info Banner */}
          <div className="mb-4 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-4 border border-purple-200 dark:border-purple-800">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💡</span>
              <div className="flex-1 text-sm">
                <p className="text-purple-900 dark:text-purple-200 font-medium mb-1">
                  How to use:
                </p>
                <ul className="text-purple-800 dark:text-purple-300 space-y-1 list-disc list-inside">
                  <li>
                    Hold the button to record your response in{' '}
                    <strong>{language === 'en' ? 'English' : 'Japanese'}</strong>
                  </li>
                  <li>
                    Slide left to cancel • Release to send
                    {language === 'ja' && ' • Slide up to check your sentence'}
                  </li>
                  {language === 'en' && (
                    <li>
                      English messages will be translated to Japanese for shadowing practice
                    </li>
                  )}
                  {language === 'ja' && (
                    <li>
                      Slide up before releasing to have AI check your Japanese for errors
                    </li>
                  )}
                  <li>Click words for details • Long-press sentences for AI explanations</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Voice Recorder */}
          <VoiceRecorder
            onSend={handleVoiceMessage}
            onCheckSentence={language === 'ja' ? handleCheckSentence : undefined}
            language={language}
          />

          {/* Loading State */}
          {sendMessageMutation.isPending && (
            <div className="mt-4 flex items-center justify-center gap-3 text-purple-600 dark:text-purple-400">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
              <span className="text-sm font-medium">AI is thinking...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
