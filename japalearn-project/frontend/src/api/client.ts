import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      // You can dispatch a global auth state update here
    }
    return Promise.reject(error);
  }
);

// API functions
export const translateText = async (data: {
  text: string;
  source: string;
  target: string;
}) => {
  const response = await api.post('/api/v1/translate', data);
  return response.data;
};

export const getWordInfo = async (word: string) => {
  const response = await api.get(`/api/v1/word/${encodeURIComponent(word)}/info`);
  return response.data;
};

export const explainSentence = async (data: {
  sentence: string;
  detail_level?: string;
}) => {
  const response = await api.post('/api/v1/word/explain', data);
  return response.data;
};

export const recognizeSpeech = async (audioFile: File, language: string = 'en') => {
  const formData = new FormData();
  formData.append('audio', audioFile);
  const response = await api.post(`/api/v1/voice/recognize?language=${language}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const generateTTS = async (data: {
  text: string;
  voice?: string;
  speed?: number;
}) => {
  const response = await api.post('/api/v1/voice/tts', data);
  return response.data;
};

export const askQuestion = async (data: {
  question: string;
  context?: Record<string, any>;
}) => {
  const response = await api.post('/api/v1/chat/ask', data);
  return response.data;
};

// Conversation Practice API
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

export const sendConversationMessage = async (data: {
  conversation_id: string;
  message: string;
  language: 'en' | 'ja';
  check_sentence?: boolean;
  audio_url?: string;
}) => {
  const response = await api.post('/api/v1/conversation/message', data);
  return response.data;
};

export const getConversationHistory = async (conversationId: string) => {
  const response = await api.get(`/api/v1/conversation/history/${conversationId}`);
  return response.data;
};

export const shadowCheck = async (data: {
  target_sentence: string;
  spoken_sentence: string;
}) => {
  const response = await api.post('/api/v1/conversation/shadow-check', data);
  return response.data;
};
