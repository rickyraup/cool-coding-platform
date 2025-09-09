'use client';

import { useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/api';

export function Header(): JSX.Element {
  const { state, setSession, setLoading, setError } = useApp();
  const { isConnected, executeCode } = useWebSocket();

  const handleNewSession = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      
      const newSession = await apiService.createSession({
        user_id: 'anonymous',
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
      
      setSession(sessionData);
      console.log('New session created:', sessionData.id);
    } catch (error) {
      console.error('Failed to create session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create session');
    } finally {
      setLoading(false);
    }
  }, [setSession, setLoading, setError]);

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
    <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold text-white">
            Code Execution Platform
          </h1>
          
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {state.currentSession && (
            <div className="text-sm text-gray-400">
              Session: {state.currentSession.id.substring(0, 8)}...
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={handleNewSession}
            className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50"
            disabled={state.isLoading}
          >
            New Session
          </button>
          
          <button 
            onClick={handleRunCode}
            className="px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:opacity-50"
            disabled={!isConnected || state.isLoading || !state.code.trim()}
          >
            Run Code
          </button>

          <button 
            onClick={handleSave}
            className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors disabled:opacity-50"
            disabled={state.isLoading}
          >
            Save
          </button>
        </div>
      </div>
    </header>
  );
}