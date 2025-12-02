import { useState, useEffect, useCallback, useMemo } from 'react';

export interface Command {
  id: string;
  label: string;
  shortcut?: string;
  category: 'navigation' | 'analysis' | 'export' | 'view' | 'help';
  action: () => void;
  disabled?: boolean;
  icon?: string;
}

interface UseCommandPaletteOptions {
  commands: Command[];
  enabled?: boolean;
}

/**
 * Custom hook for managing command palette state and search
 */
export function useCommandPalette({ commands, enabled = true }: UseCommandPaletteOptions) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');

  // Filter commands based on search query
  const filteredCommands = useMemo(() => {
    if (!query) return commands;
    
    const lowerQuery = query.toLowerCase();
    return commands.filter(cmd => {
      const labelMatch = cmd.label.toLowerCase().includes(lowerQuery);
      const categoryMatch = cmd.category.toLowerCase().includes(lowerQuery);
      return labelMatch || categoryMatch;
    });
  }, [commands, query]);

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, Command[]> = {};
    
    filteredCommands.forEach(cmd => {
      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    });
    
    return groups;
  }, [filteredCommands]);

  const open = useCallback(() => {
    setIsOpen(true);
    setQuery('');
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setQuery('');
  }, []);

  const toggle = useCallback(() => {
    if (isOpen) {
      close();
    } else {
      open();
    }
  }, [isOpen, open, close]);

  const executeCommand = useCallback((command: Command) => {
    if (!command.disabled) {
      command.action();
      close();
    }
  }, [close]);

  // Handle Ctrl+K shortcut to open command palette
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K to toggle command palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        toggle();
      }
      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        close();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled, toggle, close, isOpen]);

  return {
    isOpen,
    query,
    setQuery,
    filteredCommands,
    groupedCommands,
    open,
    close,
    toggle,
    executeCommand,
  };
}

/**
 * Category labels for display
 */
export const categoryLabels: Record<string, string> = {
  navigation: 'Navigation',
  analysis: 'Analysis',
  export: 'Export',
  view: 'View',
  help: 'Help',
};
