import { useState, useCallback, useRef } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration: number;
}

interface ToastOptions {
  message: string;
  type?: ToastType;
  duration?: number;
}

/**
 * Custom hook for managing toast notifications
 */
export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const removeToast = useCallback((id: string) => {
    // Clear timeout if exists
    const timeout = timeoutsRef.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      timeoutsRef.current.delete(id);
    }
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback(({ message, type = 'info', duration = 4000 }: ToastOptions) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    
    const newToast: Toast = {
      id,
      message,
      type,
      duration,
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-remove after duration
    if (duration > 0) {
      const timeout = setTimeout(() => {
        removeToast(id);
      }, duration);
      timeoutsRef.current.set(id, timeout);
    }

    return id;
  }, [removeToast]);

  const clearToasts = useCallback(() => {
    // Clear all timeouts
    timeoutsRef.current.forEach(timeout => clearTimeout(timeout));
    timeoutsRef.current.clear();
    setToasts([]);
  }, []);

  // Convenience methods
  const success = useCallback((message: string, duration?: number) => 
    addToast({ message, type: 'success', duration }), [addToast]);
  
  const error = useCallback((message: string, duration?: number) => 
    addToast({ message, type: 'error', duration }), [addToast]);
  
  const warning = useCallback((message: string, duration?: number) => 
    addToast({ message, type: 'warning', duration }), [addToast]);
  
  const info = useCallback((message: string, duration?: number) => 
    addToast({ message, type: 'info', duration }), [addToast]);

  return {
    toasts,
    addToast,
    removeToast,
    clearToasts,
    success,
    error,
    warning,
    info,
  };
}

// Export a type for the context
export type ToastContext = ReturnType<typeof useToasts>;
