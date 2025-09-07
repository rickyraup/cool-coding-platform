'use client';

import React, { createContext, useContext, useReducer, ReactNode } from 'react';

// Import shared types
interface CodeSession {
  id: string;
  userId: string;
  code: string;
  language: 'python';
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
}

interface TerminalLine {
  id: string;
  content: string;
  type: 'input' | 'output' | 'error';
  timestamp: Date;
}

interface AppState {
  currentSession: CodeSession | null;
  code: string;
  terminalLines: TerminalLine[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

type AppAction = 
  | { type: 'SET_SESSION'; payload: CodeSession }
  | { type: 'UPDATE_CODE'; payload: string }
  | { type: 'ADD_TERMINAL_LINE'; payload: TerminalLine }
  | { type: 'CLEAR_TERMINAL' }
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null };

const initialState: AppState = {
  currentSession: null,
  code: '# Write your Python code here\nprint("Hello, World!")',
  terminalLines: [],
  isConnected: false,
  isLoading: false,
  error: null,
};

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_SESSION':
      return {
        ...state,
        currentSession: action.payload,
        code: action.payload.code,
      };
    
    case 'UPDATE_CODE':
      return {
        ...state,
        code: action.payload,
      };
    
    case 'ADD_TERMINAL_LINE':
      return {
        ...state,
        terminalLines: [...state.terminalLines, action.payload],
      };
    
    case 'CLEAR_TERMINAL':
      return {
        ...state,
        terminalLines: [],
      };
    
    case 'SET_CONNECTED':
      return {
        ...state,
        isConnected: action.payload,
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    
    default:
      return state;
  }
};

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  // Actions
  setSession: (session: CodeSession) => void;
  updateCode: (code: string) => void;
  addTerminalLine: (content: string, type: 'input' | 'output' | 'error') => void;
  clearTerminal: () => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const actions = {
    setSession: (session: CodeSession) => {
      dispatch({ type: 'SET_SESSION', payload: session });
    },
    
    updateCode: (code: string) => {
      dispatch({ type: 'UPDATE_CODE', payload: code });
    },
    
    addTerminalLine: (content: string, type: 'input' | 'output' | 'error') => {
      const line: TerminalLine = {
        id: Date.now().toString() + Math.random().toString(36).substring(2),
        content,
        type,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_TERMINAL_LINE', payload: line });
    },
    
    clearTerminal: () => {
      dispatch({ type: 'CLEAR_TERMINAL' });
    },
    
    setConnected: (connected: boolean) => {
      dispatch({ type: 'SET_CONNECTED', payload: connected });
    },
    
    setLoading: (loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    },
    
    setError: (error: string | null) => {
      dispatch({ type: 'SET_ERROR', payload: error });
    },
  };

  return (
    <AppContext.Provider value={{ state, dispatch, ...actions }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}