import { create } from 'zustand';

interface AppState {
  currentGraphId: string | null;
  setCurrentGraphId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentGraphId: sessionStorage.getItem('currentGraphId'),
  setCurrentGraphId: (id) => {
    if (id) {
      sessionStorage.setItem('currentGraphId', id);
    } else {
      sessionStorage.removeItem('currentGraphId');
    }
    set({ currentGraphId: id });
  },
}));
