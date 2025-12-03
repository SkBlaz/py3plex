import { BrowserRouter, Routes, Route, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useMemo } from 'react';
import LoadData from './pages/LoadData';
import Visualize from './pages/Visualize';
import Analyze from './pages/Analyze';
import Export from './pages/Export';
import CommandPalette from './components/CommandPalette';
import ThemeToggle from './components/ThemeToggle';
import ToastContainer from './components/ToastContainer';
import { useCommandPalette, Command } from './hooks/useCommandPalette';
import { useDarkMode } from './hooks/useDarkMode';
import { useToasts } from './hooks/useToasts';

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, toggleTheme } = useDarkMode();
  const { toasts, removeToast } = useToasts();

  // Define all available commands
  const commands: Command[] = useMemo(() => {
    const graphId = sessionStorage.getItem('currentGraphId') || localStorage.getItem('currentGraphId');
    const hasGraph = !!graphId;

    return [
      // Navigation commands
      {
        id: 'nav-load',
        label: 'Go to Load Data',
        shortcut: 'Ctrl+1',
        category: 'navigation',
        action: () => navigate('/'),
      },
      {
        id: 'nav-visualize',
        label: 'Go to Visualize',
        shortcut: 'Ctrl+2',
        category: 'navigation',
        action: () => navigate('/visualize'),
        disabled: !hasGraph,
      },
      {
        id: 'nav-analyze',
        label: 'Go to Analyze',
        shortcut: 'Ctrl+3',
        category: 'navigation',
        action: () => navigate('/analyze'),
        disabled: !hasGraph,
      },
      {
        id: 'nav-export',
        label: 'Go to Export',
        shortcut: 'Ctrl+4',
        category: 'navigation',
        action: () => navigate('/export'),
        disabled: !hasGraph,
      },
      // View commands
      {
        id: 'view-toggle-theme',
        label: 'Toggle Dark Mode',
        category: 'view',
        action: toggleTheme,
      },
      {
        id: 'view-job-monitor',
        label: 'Open Job Monitor (Flower)',
        category: 'view',
        action: () => window.open('/flower', '_blank'),
      },
      // Help commands
      {
        id: 'help-shortcuts',
        label: 'Show Keyboard Shortcuts',
        shortcut: 'Ctrl+/',
        category: 'help',
        action: () => {
          // Dispatch a custom event that ShortcutsHelp listens for
          window.dispatchEvent(new CustomEvent('show-shortcuts-help'));
        },
      },
      {
        id: 'help-docs',
        label: 'Open Documentation',
        category: 'help',
        action: () => window.open('https://skblaz.github.io/py3plex/', '_blank'),
      },
    ];
  }, [navigate, toggleTheme, location.pathname]);

  const {
    isOpen,
    query,
    setQuery,
    groupedCommands,
    close,
    executeCommand,
  } = useCommandPalette({ commands });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <NavLink
                to="/"
                className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-900 dark:text-gray-100"
              >
                <span className="text-xl font-bold text-blue-600 dark:text-blue-400 mr-2">Py3plex</span>
                GUI
              </NavLink>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-blue-500 text-gray-900 dark:text-gray-100'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
                  }`
                }
              >
                Load Data
              </NavLink>
              <NavLink
                to="/visualize"
                className={({ isActive }) =>
                  `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-blue-500 text-gray-900 dark:text-gray-100'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
                  }`
                }
              >
                Visualize
              </NavLink>
              <NavLink
                to="/analyze"
                className={({ isActive }) =>
                  `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-blue-500 text-gray-900 dark:text-gray-100'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
                  }`
                }
              >
                Analyze
              </NavLink>
              <NavLink
                to="/export"
                className={({ isActive }) =>
                  `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-blue-500 text-gray-900 dark:text-gray-100'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
                  }`
                }
              >
                Export
              </NavLink>
            </div>
            <div className="flex items-center gap-2">
              {/* Command Palette Trigger */}
              <button
                onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))}
                className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                <span>Search...</span>
                <kbd className="px-1.5 py-0.5 text-xs bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded">⌘K</kbd>
              </button>
              
              {/* Theme Toggle */}
              <ThemeToggle theme={theme} onToggle={toggleTheme} />
              
              <a
                href="/flower"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
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

      {/* Command Palette */}
      <CommandPalette
        isOpen={isOpen}
        query={query}
        setQuery={setQuery}
        groupedCommands={groupedCommands}
        onExecute={executeCommand}
        onClose={close}
      />

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
