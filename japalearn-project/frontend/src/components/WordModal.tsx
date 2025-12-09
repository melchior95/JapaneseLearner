import { useQuery } from '@tanstack/react-query';
import { X, Volume2, Star, BookOpen } from 'lucide-react';
import { getWordInfo } from '../api/client';

interface WordModalProps {
  word: string;
  onClose: () => void;
}

interface KanjiInfo {
  character: string;
  meaning: string;
  reading: string[];
}

interface WordExample {
  japanese: string;
  english: string;
  romanji: string;
}

interface WordInfo {
  word: string;
  reading: string | null;
  romanji: string | null;
  part_of_speech: string | null;
  jlpt_level: number | null;
  definition: string | null;
  grammar_notes: Record<string, any> | null;
  kanji_breakdown: KanjiInfo[] | null;
  examples: WordExample[] | null;
}

export default function WordModal({ word, onClose }: WordModalProps) {
  const { data: wordInfo, isLoading, isError } = useQuery<WordInfo>({
    queryKey: ['word', word],
    queryFn: () => getWordInfo(word),
  });

  // Close on background click
  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Close on Escape key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackgroundClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-t-2xl">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-4xl font-bold mb-2">{word}</h2>
              {isLoading && <p className="text-blue-100">Loading...</p>}
              {wordInfo && (
                <>
                  <p className="text-2xl text-blue-100 mb-1">
                    {wordInfo.reading || '—'}
                  </p>
                  <p className="text-xl italic text-blue-200">
                    {wordInfo.romanji || '—'}
                  </p>
                </>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {isLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">
                Loading word information...
              </p>
            </div>
          )}

          {isError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
              <p className="text-red-800 dark:text-red-200">
                ❌ Failed to load word information. This word may not be in the
                database yet.
              </p>
            </div>
          )}

          {wordInfo && (
            <>
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    Part of Speech
                  </p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {wordInfo.part_of_speech || 'Unknown'}
                  </p>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-xl">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    JLPT Level
                  </p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {wordInfo.jlpt_level ? `N${wordInfo.jlpt_level}` : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Definition */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  Definition
                </h3>
                <p className="text-gray-700 dark:text-gray-300 text-lg">
                  {wordInfo.definition || 'No definition available'}
                </p>
              </div>

              {/* Kanji Breakdown */}
              {wordInfo.kanji_breakdown && wordInfo.kanji_breakdown.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    📝 Kanji Breakdown
                  </h3>
                  <div className="grid grid-cols-1 gap-3">
                    {wordInfo.kanji_breakdown.map((kanji, index) => (
                      <div
                        key={index}
                        className="bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 p-4 rounded-xl"
                      >
                        <div className="flex items-start gap-4">
                          <div className="text-4xl font-bold text-orange-600 dark:text-orange-400">
                            {kanji.character}
                          </div>
                          <div className="flex-1">
                            <p className="font-semibold text-gray-900 dark:text-white mb-1">
                              {kanji.meaning}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Readings: {kanji.reading.join(', ')}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Grammar Notes */}
              {wordInfo.grammar_notes && Object.keys(wordInfo.grammar_notes).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    📖 Grammar Notes
                  </h3>
                  <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-xl space-y-2">
                    {Object.entries(wordInfo.grammar_notes).map(([key, value]) => (
                      <div key={key}>
                        <span className="font-semibold text-green-800 dark:text-green-300 capitalize">
                          {key}:
                        </span>{' '}
                        <span className="text-gray-700 dark:text-gray-300">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Example Sentences */}
              {wordInfo.examples && wordInfo.examples.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    💬 Example Sentences
                  </h3>
                  <div className="space-y-3">
                    {wordInfo.examples.map((example, index) => (
                      <div
                        key={index}
                        className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-xl"
                      >
                        <p className="text-xl text-gray-900 dark:text-white mb-2">
                          {example.japanese}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400 italic mb-1">
                          {example.romanji}
                        </p>
                        <p className="text-gray-700 dark:text-gray-300">
                          → {example.english}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2">
                  <Volume2 className="w-5 h-5" />
                  Hear Pronunciation
                </button>
                <button className="flex-1 px-4 py-3 bg-yellow-500 hover:bg-yellow-600 text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2">
                  <Star className="w-5 h-5" />
                  Save to Favorites
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
