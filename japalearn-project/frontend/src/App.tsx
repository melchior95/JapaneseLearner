import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Languages, MessageCircle } from 'lucide-react'
import TranslationPanel from './components/TranslationPanel'
import ConversationPage from './pages/ConversationPage'
import './App.css'

function Navigation() {
  const location = useLocation()

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-lg mb-8 rounded-2xl overflow-hidden">
      <div className="flex">
        <Link
          to="/"
          className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 font-medium transition-all ${
            location.pathname === '/'
              ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
        >
          <Languages className="w-5 h-5" />
          <span>Translation</span>
        </Link>
        <Link
          to="/conversation"
          className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 font-medium transition-all ${
            location.pathname === '/conversation'
              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
        >
          <MessageCircle className="w-5 h-5" />
          <span>Conversation Practice</span>
        </Link>
      </div>
    </nav>
  )
}

function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-2">
            JapaLearn 🇯🇵
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            AI-Powered Japanese Language Learning
          </p>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main>
          <TranslationPanel />
        </main>

        {/* Footer */}
        <footer className="text-center mt-16 text-sm text-gray-500 dark:text-gray-400">
          <p>Built with React, FastAPI, and OpenAI</p>
        </footer>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/conversation" element={<ConversationPage />} />
      </Routes>
    </Router>
  )
}

export default App
