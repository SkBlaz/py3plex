import { useState, useEffect } from 'react';
import { Keyboard, X } from 'lucide-react';
import { ShortcutConfig, formatShortcut } from '../hooks/useKeyboardShortcuts';

interface ShortcutsHelpProps {
  shortcuts: ShortcutConfig[];
}

/**
 * Keyboard shortcuts help panel
 * Shows available shortcuts in a modal
 */
export default function ShortcutsHelp({ shortcuts }: ShortcutsHelpProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Filter shortcuts that have descriptions
  const documentedShortcuts = shortcuts.filter(s => s.description);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
      // Ctrl+/ to toggle help
      if (e.key === '/' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  if (documentedShortcuts.length === 0) return null;

  return (
    <>
      {/* Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-3 bg-gray-900 dark:bg-gray-700 text-white rounded-full shadow-lg hover:bg-gray-800 dark:hover:bg-gray-600 transition-colors z-40"
        title="Keyboard shortcuts (Ctrl+/)"
      >
        <Keyboard className="h-5 w-5" />
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <Keyboard className="h-6 w-6 mr-2" />
                Keyboard Shortcuts
              </h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="grid gap-4">
                {documentedShortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <span className="text-gray-900 dark:text-gray-100">{shortcut.description}</span>
                    <kbd className="px-3 py-1.5 text-sm font-semibold text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-lg shadow-sm">
                      {formatShortcut(shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Press <kbd className="px-2 py-1 text-xs font-semibold bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded">Esc</kbd> to close this dialog
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
