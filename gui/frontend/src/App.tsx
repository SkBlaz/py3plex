import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import LoadData from './pages/LoadData';
import Visualize from './pages/Visualize';
import Analyze from './pages/Analyze';
import Export from './pages/Export';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex space-x-8">
                <Link
                  to="/"
                  className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent hover:border-blue-500 text-sm font-medium text-gray-900"
                >
                  <span className="text-xl font-bold text-blue-600 mr-2">Py3plex</span>
                  GUI
                </Link>
                <Link
                  to="/"
                  className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent hover:border-blue-500 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Load Data
                </Link>
                <Link
                  to="/visualize"
                  className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent hover:border-blue-500 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Visualize
                </Link>
                <Link
                  to="/analyze"
                  className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent hover:border-blue-500 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Analyze
                </Link>
                <Link
                  to="/export"
                  className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent hover:border-blue-500 text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Export
                </Link>
              </div>
              <div className="flex items-center">
                <a
                  href="/flower"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-500 hover:text-gray-900"
                >
                  Job Monitor
                </a>
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<LoadData />} />
            <Route path="/visualize" element={<Visualize />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/export" element={<Export />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
