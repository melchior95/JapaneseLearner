import { useQuery } from '@tanstack/react-query';
import { X, Volume2, Sparkles, BookOpen, Languages } from 'lucide-react';
import { explainSentence } from '../api/client';
import { useTTS } from '../hooks/useTTS';

interface ExplanationModalProps {
  sentence: string;
  onClose: () => void;
}

interface GrammarBreakdown {
  part: string;
  role: string;
  explanation: string;
}

interface ExplanationData {
  sentence: string;
  explanation: string;
  grammar_breakdown: GrammarBreakdown[];
  cultural_context?: string;
  alternative_phrasings?: string[];
}

export default function ExplanationModal({ sentence, onClose }: ExplanationModalProps) {
  const { data: explanation, isLoading, isError } = useQuery<ExplanationData>({
    queryKey: ['explain', sentence],
    queryFn: () => explainSentence({ sentence, detail_level: 'comprehensive' }),
  });

  const { isPlaying, isLoading: ttsLoading, play: playTTS, stop: stopTTS } = useTTS();

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

  const handlePlayExplanation = () => {
    if (isPlaying) {
      stopTTS();
    } else if (explanation) {
      playTTS(explanation.explanation);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
      onClick={handleBackgroundClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 rounded-t-2xl">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-6 h-6" />
                <h2 className="text-2xl font-bold">AI Grammar Explanation</h2>
              </div>
              <p className="text-3xl font-medium text-white mb-2">{sentence}</p>
              <p className="text-purple-100 text-sm">Long-press activated • Powered by GPT-4</p>
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
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mb-4"></div>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                ✨ AI is analyzing the grammar...
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                This may take a few seconds
              </p>
            </div>
          )}

          {isError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
              <p className="text-red-800 dark:text-red-200 text-lg">
                ❌ Failed to generate explanation. Please make sure your OpenAI API key is configured.
              </p>
            </div>
          )}

          {explanation && (
            <>
              {/* Main Explanation */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <BookOpen className="w-5 h-5" />
                    Overall Explanation
                  </h3>
                  <button
                    onClick={handlePlayExplanation}
                    disabled={ttsLoading}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Volume2 className="w-4 h-4" />
                    {isPlaying ? 'Stop' : ttsLoading ? 'Loading...' : 'Listen'}
                  </button>
                </div>
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-6 rounded-xl">
                  <p className="text-lg text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                    {explanation.explanation}
                  </p>
                </div>
              </div>

              {/* Grammar Breakdown */}
              {explanation.grammar_breakdown && explanation.grammar_breakdown.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    📝 Detailed Grammar Breakdown
                  </h3>
                  <div className="space-y-4">
                    {explanation.grammar_breakdown.map((item, index) => (
                      <div
                        key={index}
                        className="bg-white dark:bg-gray-700 border-l-4 border-purple-500 p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-300 rounded-full flex items-center justify-center font-bold">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-baseline gap-3 mb-2">
                              <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                                {item.part}
                              </span>
                              <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 text-sm font-medium rounded-full">
                                {item.role}
                              </span>
                            </div>
                            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                              {item.explanation}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cultural Context */}
              {explanation.cultural_context && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    🌏 Cultural Context
                  </h3>
                  <div className="bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 p-6 rounded-xl border-l-4 border-orange-500">
                    <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                      {explanation.cultural_context}
                    </p>
                  </div>
                </div>
              )}

              {/* Alternative Phrasings */}
              {explanation.alternative_phrasings && explanation.alternative_phrasings.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Languages className="w-5 h-5" />
                    Alternative Ways to Say This
                  </h3>
                  <div className="space-y-3">
                    {explanation.alternative_phrasings.map((phrase, index) => (
                      <div
                        key={index}
                        className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800"
                      >
                        <p className="text-lg text-gray-800 dark:text-gray-200">
                          {index + 1}. {phrase}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tips Section */}
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-5 rounded-xl">
                <h4 className="font-semibold text-green-800 dark:text-green-300 mb-2 flex items-center gap-2">
                  💡 Learning Tip
                </h4>
                <p className="text-green-700 dark:text-green-300">
                  Try creating your own sentences using the same grammar patterns explained above.
                  Practice makes perfect!
                </p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4 rounded-b-2xl">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
            <span>💬 Long-press any sentence for AI explanations</span>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
