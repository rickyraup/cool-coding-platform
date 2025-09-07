'use client';

import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function Header() {
  const { state, updateCode } = useApp();
  const { isConnected, executeCode } = useWebSocket();

  const handleNewSession = async () => {
    // TODO: Create new session via API
    console.log('Creating new session...');
  };

  const handleRunCode = () => {
    if (state.code.trim()) {
      executeCode(state.code, 'main.py');
    }
  };

  const handleSave = async () => {
    // TODO: Save current session
    console.log('Saving session...');
  };

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