'use client';

import type { ReactNode} from 'react';
import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';

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
  command?: string;
}

export interface FileItem {
  name: string;
  type: 'file' | 'directory';
  path: string;
}

interface AppState {
  currentSession: CodeSession | null;
  code: string;
  terminalLines: TerminalLine[];
  files: FileItem[];
  currentFile: string | null;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  isAutosaveEnabled: boolean;
  hasUnsavedChanges: boolean;
  lastSavedCode: string;
}

type AppAction = 
  | { type: 'SET_SESSION'; payload: CodeSession | null }
  | { type: 'UPDATE_CODE'; payload: string }
  | { type: 'ADD_TERMINAL_LINE'; payload: TerminalLine }
  | { type: 'CLEAR_TERMINAL' }
  | { type: 'SET_FILES'; payload: FileItem[] }
  | { type: 'SET_CURRENT_FILE'; payload: string | null }
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_AUTOSAVE_ENABLED'; payload: boolean }
  | { type: 'MARK_SAVED'; payload: string }
  | { type: 'CLEAR_UNSAVED_CHANGES' };

const initialState: AppState = {
  currentSession: null,
  code: '',
  terminalLines: [],
  files: [],
  currentFile: null,
  isConnected: false,
  isLoading: false,
  error: null,
  isAutosaveEnabled: true,
  hasUnsavedChanges: false,
  lastSavedCode: '',
};

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_SESSION':
      return {
        ...state,
        currentSession: action.payload,
        code: action.payload?.code ?? '',
      };
    
    case 'UPDATE_CODE':
      return {
        ...state,
        code: action.payload,
        hasUnsavedChanges: action.payload !== state.lastSavedCode,
      };
    
    case 'ADD_TERMINAL_LINE':
      console.log('🔍 [AppContext] Reducer ADD_TERMINAL_LINE:', action.payload);
      console.log('🔍 [AppContext] Current terminalLines count:', state.terminalLines.length);
      const newState = {
        ...state,
        terminalLines: [...state.terminalLines, action.payload],
      };
      console.log('🔍 [AppContext] New terminalLines count:', newState.terminalLines.length);
      return newState;
    
    case 'CLEAR_TERMINAL':
      return {
        ...state,
        terminalLines: [],
      };
    
    case 'SET_FILES':
      return {
        ...state,
        files: action.payload,
      };
    
    case 'SET_CURRENT_FILE':
      return {
        ...state,
        currentFile: action.payload,
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
    
    case 'SET_AUTOSAVE_ENABLED':
      return {
        ...state,
        isAutosaveEnabled: action.payload,
      };
    
    case 'MARK_SAVED':
      return {
        ...state,
        lastSavedCode: action.payload,
        hasUnsavedChanges: false,
      };
    
    case 'CLEAR_UNSAVED_CHANGES':
      return {
        ...state,
        hasUnsavedChanges: false,
      };
    
    default:
      return state;
  }
};

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  // Actions
  setSession: (session: CodeSession | null) => void;
  updateCode: (code: string) => void;
  addTerminalLine: (content: string, type: 'input' | 'output' | 'error', command?: string) => void;
  clearTerminal: () => void;
  setFiles: (files: FileItem[]) => void;
  setCurrentFile: (path: string | null) => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setAutosaveEnabled: (enabled: boolean) => void;
  markSaved: (code: string) => void;
  clearUnsavedChanges: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Session management is now handled manually through authentication and workspace selection
  // No longer auto-create sessions on app startup since we have proper user-based session management
  useEffect(() => {
    console.log('AppContext initialized - session management handled by authentication system');
    // Sessions are now created/loaded explicitly when users navigate to workspaces
  }, []); // Only run on mount

  const actions = {
    setSession: useCallback((session: CodeSession | null) => {
      dispatch({ type: 'SET_SESSION', payload: session });
    }, []),
    
    updateCode: useCallback((code: string) => {
      dispatch({ type: 'UPDATE_CODE', payload: code });
    }, []),
    
    addTerminalLine: useCallback((content: string, type: 'input' | 'output' | 'error', command?: string) => {
      console.log('🔍 [AppContext] addTerminalLine called:', { content, type, command });
      const line: TerminalLine = {
        id: Date.now().toString() + Math.random().toString(36).substring(2),
        content,
        type,
        timestamp: new Date(),
        ...(command !== undefined && { command }),
      };
      console.log('🔍 [AppContext] Created terminal line:', line);
      dispatch({ type: 'ADD_TERMINAL_LINE', payload: line });
    }, []),
    
    clearTerminal: useCallback(() => {
      dispatch({ type: 'CLEAR_TERMINAL' });
    }, []),
    
    setFiles: useCallback((files: FileItem[]) => {
      dispatch({ type: 'SET_FILES', payload: files });
    }, []),
    
    setCurrentFile: useCallback((path: string | null) => {
      dispatch({ type: 'SET_CURRENT_FILE', payload: path });
    }, []),
    
    setConnected: useCallback((connected: boolean) => {
      dispatch({ type: 'SET_CONNECTED', payload: connected });
    }, []),
    
    setLoading: useCallback((loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    }, []),
    
    setError: useCallback((error: string | null) => {
      dispatch({ type: 'SET_ERROR', payload: error });
    }, []),
    
    setAutosaveEnabled: useCallback((enabled: boolean) => {
      dispatch({ type: 'SET_AUTOSAVE_ENABLED', payload: enabled });
    }, []),
    
    markSaved: useCallback((code: string) => {
      dispatch({ type: 'MARK_SAVED', payload: code });
    }, []),
    
    clearUnsavedChanges: useCallback(() => {
      dispatch({ type: 'CLEAR_UNSAVED_CHANGES' });
    }, []),
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