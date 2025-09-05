'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function Terminal() {
  const { state, clearTerminal } = useApp();
  const { sendTerminalCommand } = useWebSocket();
  
  const [currentInput, setCurrentInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const handleSubmit = useCallback(() => {
    if (!currentInput.trim()) return;
    
    // Add to command history
    setCommandHistory(prev => [...prev, currentInput]);
    setHistoryIndex(-1);
    
    // Handle local commands
    if (currentInput === 'clear') {
      clearTerminal();
      setCurrentInput('');
      return;
    }
    
    // Send command via WebSocket
    sendTerminalCommand(currentInput);
    setCurrentInput('');
  }, [currentInput, sendTerminalCommand, clearTerminal]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        setCurrentInput(commandHistory[commandHistory.length - 1 - newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setCurrentInput(commandHistory[commandHistory.length - 1 - newIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setCurrentInput('');
      }
    }
  }, [handleSubmit, historyIndex, commandHistory]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [state.terminalLines]);

  // Focus input when terminal is clicked
  const focusInput = useCallback(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div 
      className="h-full flex flex-col bg-black text-green-400 font-mono text-sm cursor-text"
      onClick={focusInput}
    >
      <div 
        ref={terminalRef}
        className="flex-1 p-4 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
      >
        {state.terminalLines.map((line) => (
          <div 
            key={line.id} 
            className={`mb-1 ${
              line.type === 'input' ? 'text-white' : 
              line.type === 'error' ? 'text-red-400' : 
              'text-green-400'
            }`}
          >
            {line.content}
          </div>
        ))}
        
        {/* Current input line */}
        <div className="flex items-center text-white">
          <span className="text-green-400 mr-1">$</span>
          <input
            ref={inputRef}
            type="text"
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent outline-none border-none text-white font-mono"
            placeholder="Enter command..."
            autoFocus
          />
        </div>
      </div>
    </div>
  );
}