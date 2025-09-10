'use client';

import { useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/api';

export function Header(): JSX.Element {
  const { state, setSession, setLoading, setError, clearTerminal, setFiles, setCurrentFile, updateCode } = useApp();
  const { isConnected, executeCode } = useWebSocket();

  const handleNewSession = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      
      // Clear current environment
      clearTerminal();
      setFiles([]);
      setCurrentFile(null);
      
      const newSession = await apiService.createSession({
        user_id: 'user-' + Date.now(),
        code: '# Write your Python code here\nprint("Hello, World!")',
        language: 'python'
      });
      
      // Convert API response to internal format
      const sessionData = {
        id: newSession.id,
        userId: newSession.user_id,
        code: newSession.code,
        language: 'python' as const,
        createdAt: new Date(newSession.created_at),
        updatedAt: new Date(newSession.updated_at),
        isActive: newSession.is_active,
      };
      
      // Set the new session and update code
      setSession(sessionData);
      updateCode(newSession.code);
      
      console.log('New session created:', sessionData.id);
      
      // Add terminal message about new session
      setTimeout(() => {
        // We need to use the addTerminalLine from the context, but we don't have direct access here
        // The WebSocket connection will handle this when it reconnects
      }, 100);
      
    } catch (error) {
      console.error('Failed to create session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create session');
    } finally {
      setLoading(false);
    }
  }, [setSession, setLoading, setError, clearTerminal, setFiles, setCurrentFile, updateCode]);

  const handleRunCode = useCallback((): void => {
    if (state.code.trim()) {
      executeCode(state.code, 'main.py');
    }
  }, [state.code, executeCode]);

  const handleSave = useCallback(async (): Promise<void> => {
    if (!state.currentSession) {
      console.warn('No session to save');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const updatedSession = await apiService.updateSession(state.currentSession.id, {
        code: state.code,
        is_active: true,
      });
      
      // Convert API response to internal format
      const sessionData = {
        id: updatedSession.id,
        userId: updatedSession.user_id,
        code: updatedSession.code,
        language: 'python' as const,
        createdAt: new Date(updatedSession.created_at),
        updatedAt: new Date(updatedSession.updated_at),
        isActive: updatedSession.is_active,
      };
      
      setSession(sessionData);
      console.log('Session saved:', sessionData.id);
    } catch (error) {
      console.error('Failed to save session:', error);
      setError(error instanceof Error ? error.message : 'Failed to save session');
    } finally {
      setLoading(false);
    }
  }, [state.currentSession, state.code, setSession, setLoading, setError]);

  return (
    <header className="bg-gradient-to-r from-gray-800 to-gray-750 border-b border-gray-600 px-6 py-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <h1 className="text-xl font-bold text-white tracking-tight">
            Code Execution Platform
          </h1>
          
          <div className="flex items-center space-x-3 bg-gray-700/50 px-3 py-1.5 rounded-lg">
            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-red-400 shadow-sm shadow-red-400/50'}`} />
            <span className={`text-sm font-medium ${isConnected ? 'text-emerald-300' : 'text-red-300'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {state.currentSession && (
            <div className="bg-blue-500/20 px-3 py-1.5 rounded-lg border border-blue-400/30">
              <span className="text-sm font-mono text-blue-300">
                Session: {state.currentSession.id.substring(0, 8)}...
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={handleNewSession}
            className="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            disabled={state.isLoading}
          >
            New Session
          </button>
          
          <button 
            onClick={handleRunCode}
            className="px-4 py-2 text-sm font-medium bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            disabled={!isConnected || state.isLoading || !state.code.trim()}
          >
            ▶ Run Code
          </button>

          <button 
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium bg-gray-600 hover:bg-gray-500 active:bg-gray-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            disabled={state.isLoading}
          >
            💾 Save
          </button>
        </div>
      </div>
    </header>
  );
}