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
  type: 'input' | 'output' | 'error' | 'pod_ready' | 'clear_progress';
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
  hasUnsavedChanges: boolean;
  lastSavedCode: string;
  // File content cache for multiple files
  fileContents: Record<string, string>;
  fileSavedStates: Record<string, string>;
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
  | { type: 'MARK_SAVED'; payload: string }
  | { type: 'CLEAR_UNSAVED_CHANGES' }
  | { type: 'SET_FILE_CONTENT'; payload: { filePath: string; content: string } }
  | { type: 'CACHE_CURRENT_FILE_CONTENT' }
  | { type: 'LOAD_FILE_CONTENT'; payload: string }
  | { type: 'RESET_ALL_STATE' };

const initialState: AppState = {
  currentSession: null,
  code: '',
  terminalLines: [],
  files: [],
  currentFile: null,
  isConnected: false,
  isLoading: false,
  error: null,
  hasUnsavedChanges: false,
  lastSavedCode: '',
  fileContents: {},
  fileSavedStates: {},
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
        // Also update fileContents for the current file to track unsaved changes
        fileContents: state.currentFile
          ? {
              ...state.fileContents,
              [state.currentFile]: action.payload,
            }
          : state.fileContents,
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
    
    case 'SET_FILES':
      return {
        ...state,
        files: action.payload,
      };
    
    case 'SET_CURRENT_FILE':
      // Cache current file content before switching if there was a previous file
      const updatedFileContents = state.currentFile && state.currentFile !== action.payload
        ? {
            ...state.fileContents,
            [state.currentFile]: state.code,
          }
        : state.fileContents;

      // Load content for new file if available in cache
      const newFileContent = updatedFileContents[action.payload ?? ''] ?? '';

      return {
        ...state,
        fileContents: updatedFileContents,
        currentFile: action.payload,
        code: newFileContent,
        hasUnsavedChanges: newFileContent !== (state.fileSavedStates[action.payload ?? ''] ?? ''),
        lastSavedCode: state.fileSavedStates[action.payload ?? ''] ?? '',
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

    case 'MARK_SAVED':
      return {
        ...state,
        lastSavedCode: action.payload,
        hasUnsavedChanges: false,
        // Update the saved state for the current file
        fileSavedStates: state.currentFile
          ? {
              ...state.fileSavedStates,
              [state.currentFile]: action.payload,
            }
          : state.fileSavedStates,
      };
    
    case 'CLEAR_UNSAVED_CHANGES':
      return {
        ...state,
        hasUnsavedChanges: false,
      };

    case 'SET_FILE_CONTENT':
      const { filePath, content } = action.payload;
      return {
        ...state,
        fileContents: {
          ...state.fileContents,
          [filePath]: content,
        },
        fileSavedStates: {
          ...state.fileSavedStates,
          [filePath]: content,
        },
        // Update current code if this is the current file
        ...(state.currentFile === filePath && {
          code: content,
          hasUnsavedChanges: false,
          lastSavedCode: content,
        }),
      };

    case 'CACHE_CURRENT_FILE_CONTENT':
      if (!state.currentFile) return state;
      return {
        ...state,
        fileContents: {
          ...state.fileContents,
          [state.currentFile]: state.code,
        },
      };

    case 'LOAD_FILE_CONTENT':
      const fileContent = action.payload;
      return {
        ...state,
        code: fileContent,
        hasUnsavedChanges: false,
        lastSavedCode: fileContent,
        // Update both fileContents and fileSavedStates when loading from backend
        fileContents: state.currentFile
          ? {
              ...state.fileContents,
              [state.currentFile]: fileContent,
            }
          : state.fileContents,
        fileSavedStates: state.currentFile
          ? {
              ...state.fileSavedStates,
              [state.currentFile]: fileContent,
            }
          : state.fileSavedStates,
      };

    case 'RESET_ALL_STATE':
      return {
        ...initialState,
        // Keep connection state and loading state as they're not workspace-specific
        isConnected: state.isConnected,
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
  addTerminalLine: (content: string, type: 'input' | 'output' | 'error' | 'clear_progress' | 'pod_ready', command?: string) => void;
  clearTerminal: () => void;
  setFiles: (files: FileItem[]) => void;
  setCurrentFile: (path: string | null) => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  markSaved: (code: string) => void;
  clearUnsavedChanges: () => void;
  // File content management
  setFileContent: (filePath: string, content: string) => void;
  cacheCurrentFileContent: () => void;
  loadFileContent: (content: string) => void;
  // Complete state reset for workspace switching
  resetAllState: () => void;
  // Helper to check if a file has unsaved changes
  hasFileUnsavedChanges: (filePath: string) => boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Session management is now handled manually through authentication and workspace selection
  // No longer auto-create sessions on app startup since we have proper user-based session management
  useEffect(() => {
    // Sessions are now created/loaded explicitly when users navigate to workspaces
  }, []); // Only run on mount

  const actions = {
    setSession: useCallback((session: CodeSession | null) => {
      dispatch({ type: 'SET_SESSION', payload: session });
    }, []),
    
    updateCode: useCallback((code: string) => {
      dispatch({ type: 'UPDATE_CODE', payload: code });
    }, []),
    
    addTerminalLine: useCallback((content: string, type: 'input' | 'output' | 'error' | 'clear_progress' | 'pod_ready', command?: string) => {
      const line: TerminalLine = {
        id: Date.now().toString() + Math.random().toString(36).substring(2),
        content,
        type,
        timestamp: new Date(),
        ...(command !== undefined && { command }),
      };
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

    markSaved: useCallback((code: string) => {
      dispatch({ type: 'MARK_SAVED', payload: code });
    }, []),
    
    clearUnsavedChanges: useCallback(() => {
      dispatch({ type: 'CLEAR_UNSAVED_CHANGES' });
    }, []),

    setFileContent: useCallback((filePath: string, content: string) => {
      dispatch({ type: 'SET_FILE_CONTENT', payload: { filePath, content } });
    }, []),

    cacheCurrentFileContent: useCallback(() => {
      dispatch({ type: 'CACHE_CURRENT_FILE_CONTENT' });
    }, []),

    loadFileContent: useCallback((content: string) => {
      dispatch({ type: 'LOAD_FILE_CONTENT', payload: content });
    }, []),

    resetAllState: useCallback(() => {
      dispatch({ type: 'RESET_ALL_STATE' });
    }, []),

    hasFileUnsavedChanges: useCallback((filePath: string): boolean => {
      // Check if the file has unsaved changes by comparing current content with saved state
      const currentContent = state.fileContents[filePath];
      const savedContent = state.fileSavedStates[filePath];

      // If we don't have current content, the file hasn't been modified
      if (currentContent === undefined) return false;

      // Compare with saved state (undefined saved state means never saved, so it has changes if there's content)
      return currentContent !== (savedContent ?? '');
    }, [state.fileContents, state.fileSavedStates]),
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