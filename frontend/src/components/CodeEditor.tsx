'use client';

import { useCallback, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export function CodeEditor() {
  const { state, updateCode } = useApp();

  const handleCodeChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateCode(e.target.value);
  }, [updateCode]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      
      const newValue = state.code.substring(0, start) + '    ' + state.code.substring(end);
      updateCode(newValue);
      
      // Reset cursor position
      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 4;
      }, 0);
    }
  }, [state.code, updateCode]);

  return (
    <div className="h-full flex flex-col">
      <textarea
        value={state.code}
        onChange={handleCodeChange}
        onKeyDown={handleKeyDown}
        className="flex-1 w-full p-4 bg-gray-900 text-white font-mono text-sm resize-none outline-none border-none"
        placeholder="Write your Python code here..."
        spellCheck={false}
        style={{
          tabSize: 4,
          fontFamily: 'ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace'
        }}
      />
      
      <div className="bg-gray-800 border-t border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          <span>Python</span>
          <span>•</span>
          <span>UTF-8</span>
          <span>•</span>
          <span>Line {state.code.split('\n').length}</span>
          {state.currentSession && (
            <>
              <span>•</span>
              <span>Session: {state.currentSession.id.substring(0, 8)}</span>
            </>
          )}
        </div>
        
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          {state.error && (
            <span className="text-red-400">Error: {state.error}</span>
          )}
          <span>{state.code.length} characters</span>
        </div>
      </div>
    </div>
  );
}