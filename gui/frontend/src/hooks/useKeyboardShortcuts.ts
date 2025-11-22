import { useEffect } from 'react';

export interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description?: string;
}

/**
 * Custom hook for registering keyboard shortcuts
 * 
 * @param shortcuts - Array of shortcut configurations
 * @param enabled - Whether shortcuts are enabled (default: true)
 */
export function useKeyboardShortcuts(
  shortcuts: ShortcutConfig[],
  enabled: boolean = true
) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl === undefined || shortcut.ctrl === (event.ctrlKey || event.metaKey);
        const shiftMatch = shortcut.shift === undefined || shortcut.shift === event.shiftKey;
        const altMatch = shortcut.alt === undefined || shortcut.alt === event.altKey;
        
        // Use exact match for special keys, case-insensitive for letters
        const eventKey = event.key;
        const shortcutKey = shortcut.key;
        const keyMatch = eventKey.length === 1 && shortcutKey.length === 1
          ? eventKey.toLowerCase() === shortcutKey.toLowerCase()
          : eventKey === shortcutKey;

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          event.preventDefault();
          shortcut.action();
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, enabled]);
}

/**
 * Format keyboard shortcut for display
 * @param config - Shortcut configuration
 * @returns Formatted string like "Ctrl+U" or "Shift+Enter"
 */
export function formatShortcut(config: ShortcutConfig): string {
  const parts: string[] = [];
  if (config.ctrl) parts.push('Ctrl');
  if (config.shift) parts.push('Shift');
  if (config.alt) parts.push('Alt');
  
  // Keep special keys as-is, only uppercase single letters
  const key = config.key.length === 1 ? config.key.toUpperCase() : config.key;
  parts.push(key);
  
  return parts.join('+');
}
