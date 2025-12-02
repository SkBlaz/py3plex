import { useEffect, useRef, useState } from 'react';
import { Search, Command, ArrowRight, FileText, BarChart2, Download, Eye, HelpCircle, X } from 'lucide-react';
import { Command as CommandType, categoryLabels } from '../hooks/useCommandPalette';

interface CommandPaletteProps {
  isOpen: boolean;
  query: string;
  setQuery: (query: string) => void;
  groupedCommands: Record<string, CommandType[]>;
  onExecute: (command: CommandType) => void;
  onClose: () => void;
}

const categoryIcons: Record<string, React.ReactNode> = {
  navigation: <ArrowRight className="h-4 w-4" />,
  analysis: <BarChart2 className="h-4 w-4" />,
  export: <Download className="h-4 w-4" />,
  view: <Eye className="h-4 w-4" />,
  help: <HelpCircle className="h-4 w-4" />,
};

/**
 * Command Palette component - Quick access to all actions via Ctrl+K
 */
export default function CommandPalette({
  isOpen,
  query,
  setQuery,
  groupedCommands,
  onExecute,
  onClose,
}: CommandPaletteProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Flatten commands for keyboard navigation
  const flatCommands = Object.values(groupedCommands).flat();

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < flatCommands.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : flatCommands.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (flatCommands[selectedIndex]) {
            onExecute(flatCommands[selectedIndex]);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, flatCommands, selectedIndex, onExecute]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current && flatCommands.length > 0) {
      const items = listRef.current.querySelectorAll('[data-command-item]');
      const selectedItem = items[selectedIndex] as HTMLElement | undefined;
      selectedItem?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [selectedIndex, flatCommands.length]);

  if (!isOpen) return null;

  const categories = Object.keys(groupedCommands);
  let globalIndex = 0;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 dark:bg-black/70 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-start justify-center p-4 pt-[15vh]">
        <div className="relative w-full max-w-xl transform overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-2xl ring-1 ring-black/5 transition-all">
          {/* Search Input */}
          <div className="flex items-center border-b border-gray-200 dark:border-gray-700 px-4">
            <Command className="h-5 w-5 text-gray-400 dark:text-gray-500" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a command or search..."
              className="h-14 w-full border-0 bg-transparent pl-4 pr-4 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-0 text-sm"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Commands List */}
          <div 
            ref={listRef}
            className="max-h-80 overflow-y-auto p-2"
          >
            {categories.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                <Search className="h-8 w-8 mx-auto mb-2 text-gray-400 dark:text-gray-500" />
                <p>No commands found</p>
                <p className="text-xs mt-1">Try a different search term</p>
              </div>
            ) : (
              categories.map((category) => (
                <div key={category} className="mb-2">
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                    {categoryIcons[category]}
                    {categoryLabels[category] || category}
                  </div>
                  {groupedCommands[category].map((command) => {
                    const index = globalIndex++;
                    const isSelected = index === selectedIndex;
                    
                    return (
                      <button
                        key={command.id}
                        data-command-item
                        onClick={() => onExecute(command)}
                        disabled={command.disabled}
                        className={`w-full flex items-center justify-between px-3 py-2.5 text-sm rounded-lg transition-colors ${
                          isSelected
                            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                        } ${
                          command.disabled 
                            ? 'opacity-50 cursor-not-allowed' 
                            : 'cursor-pointer'
                        }`}
                      >
                        <span className="flex items-center gap-3">
                          <FileText className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                          {command.label}
                        </span>
                        {command.shortcut && (
                          <kbd className="ml-auto px-2 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">
                            {command.shortcut}
                          </kbd>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-xs">↑↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-xs">↵</kbd>
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-xs">Esc</kbd>
                Close
              </span>
            </div>
            <span>
              {flatCommands.length} command{flatCommands.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
