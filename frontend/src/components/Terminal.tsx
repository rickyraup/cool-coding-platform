'use client';

import { useCallback, useRef, useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function Terminal(): JSX.Element {
  const { state, clearTerminal } = useApp();
  const { sendTerminalCommand, isConnected } = useWebSocket();
  
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);
  const [currentLine, setCurrentLine] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [cursorX, setCursorX] = useState(0);
  const lastEnterTimeRef = useRef(0);

  // Initialize xterm
  useEffect(() => {
    if (typeof window === 'undefined' || !terminalRef.current || xtermRef.current) return;
  
    const lastEnterTimeRef = { current: 0 };
    const lastBackspaceTimeRef = { current: 0 };
  
    const initializeTerminal = async () => {
      try {
        const [
          { Terminal },
          { FitAddon },
          { WebLinksAddon }
        ] = await Promise.all([
          import('@xterm/xterm'),
          import('@xterm/addon-fit'),
          import('@xterm/addon-web-links')
        ]);
  
        await import('@xterm/xterm/css/xterm.css');
  
        const terminal = new Terminal({
          theme: {
            background: '#0f0f23',
            foreground: '#cccccc',
            cursor: '#64ffda',
            cursorAccent: '#1a1a2e',
            black: '#000000',
            red: '#ff6b6b',
            green: '#51cf66',
            yellow: '#ffd43b',
            blue: '#339af0',
            magenta: '#e599f7',
            cyan: '#64ffda',
            white: '#f8f9fa',
            brightBlack: '#495057',
            brightRed: '#ff8787',
            brightGreen: '#69db7c',
            brightYellow: '#ffe066',
            brightBlue: '#4dabf7',
            brightMagenta: '#da77f2',
            brightCyan: '#77eeff',
            brightWhite: '#ffffff',
            selectionBackground: '#364954',
            selectionForeground: '#ffffff'
          },
          fontFamily: '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
          fontSize: 14,
          lineHeight: 1.4,
          cursorBlink: true,
          cursorStyle: 'block',
          cursorWidth: 2,
          scrollback: 5000,
          tabStopWidth: 4,
          allowTransparency: true,
        });
  
        const fitAddon = new FitAddon();
        const webLinksAddon = new WebLinksAddon();
  
        terminal.loadAddon(fitAddon);
        terminal.loadAddon(webLinksAddon);
  
        if (terminalRef.current) {
          terminal.open(terminalRef.current);
          fitAddon.fit();
  
          setTimeout(() => {
            terminal.focus();
            console.log('🎯 [Terminal] Terminal focused for keyboard input');
          }, 100);
        }
  
        terminal.writeln('\x1b[36m╭─────────────────────────────────────────╮\x1b[0m');
        terminal.writeln('\x1b[36m│    \x1b[32mCode Execution Platform Terminal\x1b[36m    │\x1b[0m');
        terminal.writeln('\x1b[36m│  \x1b[33mType commands or "help" for available\x1b[36m  │\x1b[0m');
        terminal.writeln('\x1b[36m│              \x1b[33mcommands.\x1b[36m               │\x1b[0m');
        terminal.writeln('\x1b[36m╰─────────────────────────────────────────╯\x1b[0m');
        terminal.write('\x1b[32m$ \x1b[0m');
  
        xtermRef.current = terminal;
        fitAddonRef.current = fitAddon;
  
        terminal.onData((data: string): void => {
          const terminal = xtermRef.current;
          if (!terminal) return;
  
          const now = Date.now();
  
          if (data === '\r') { // Enter key
            if (now - lastEnterTimeRef.current < 100) {
              console.log('🚫 [Terminal] Duplicate Enter key ignored');
              return;
            }
            lastEnterTimeRef.current = now;
            
            // Get current line and handle command
            const cmdToExecute = currentLine.trim();
            console.log('🔥 [Terminal] Enter pressed, executing command:', JSON.stringify(cmdToExecute));
            
            // Clear the current line immediately
            setCurrentLine('');
            setCursorX(0);
            
            // Execute command
            setTimeout(() => handleCommand(cmdToExecute), 0);
            return;
          }
  
          if (data === '\u007F' || data === '\b' || data === '\u0008') {
            setCurrentLine(prev => {
              if (prev.length > 0) {
                const newLine = prev.slice(0, -1);
                replaceCurrentLine(newLine);
                setCursorX(newLine.length);
                return newLine;
              }
              return prev; // no change if already empty
            });
            return;
          }
          
          
  
          if (data === '\u001b[A') { // Up arrow
            if (commandHistory.length > 0) {
              const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1);
              if (newIndex !== historyIndex) {
                setHistoryIndex(newIndex);
                const cmd = commandHistory[commandHistory.length - 1 - newIndex] ?? '';
                replaceCurrentLine(cmd);
              }
            }
            return;
          }
  
          if (data === '\u001b[B') { // Down arrow
            if (historyIndex >= 0) {
              const newIndex = historyIndex - 1;
              setHistoryIndex(newIndex);
              const cmd = newIndex >= 0 ?
                commandHistory[commandHistory.length - 1 - newIndex] ?? '' : '';
              replaceCurrentLine(cmd);
            }
            return;
          }
  
          if (data === '\u0003') { // Ctrl+C
            terminal.write('^C\r\n$ ');
            setCurrentLine('');
            setCursorX(0);
            return;
          }
  
          if (data >= ' ' || data === '\t') {
            // Reset debounce timers on normal input
            lastBackspaceTimeRef.current = 0;
            lastEnterTimeRef.current = 0;
  
            setCurrentLine(prev => {
              const newLine = prev + data;
              return newLine;
            });
            setCursorX(prev => prev + 1);
            terminal.write(data);
          } else {
            console.log('🚫 [Terminal] Character ignored:', JSON.stringify(data), 'charCode:', data.charCodeAt(0));
          }
        });
  
        const handleResize = (): void => {
          if (fitAddonRef.current && xtermRef.current) {
            fitAddonRef.current.fit();
          }
        };
  
        window.addEventListener('resize', handleResize);
  
        return () => {
          window.removeEventListener('resize', handleResize);
          if (terminal) {
            terminal.dispose();
          }
          xtermRef.current = null;
          fitAddonRef.current = null;
        };
      } catch (error) {
        console.error('Failed to initialize terminal:', error);
      }
    };
  
    initializeTerminal();
  }, []);
  

  const replaceCurrentLine = useCallback((newLine: string): void => {
    const terminal = xtermRef.current;
    if (!terminal) return;
  
    // Clear line: return cursor to start, write prompt + enough spaces to overwrite old line, return cursor again
    terminal.write('\r\x1b[32m$ \x1b[0m'); // write prompt
    terminal.write(' '.repeat(currentLine.length)); // clear old line by writing spaces
    terminal.write('\r\x1b[32m$ \x1b[0m'); // write prompt again
  
    // Write new line
    terminal.write(newLine);
  }, [currentLine]);
  

  const lastCommandRef = useRef<string | null>(null);

  const handleCommand = useCallback((command: string): void => {
    if (lastCommandRef.current === command) {
      console.log('🚫 Skipping duplicate command:', command);
      return;
    }

    lastCommandRef.current = command;

    const terminal = xtermRef.current;
    if (!terminal) return;

    terminal.write('\r\n');

    if (!command.trim()) {
      terminal.write('\x1b[32m$ \x1b[0m');
      setCursorX(0);
      // Clear lastCommand after a small delay so repeated empty commands work
      setTimeout(() => lastCommandRef.current = null, 100);
      return;
    }

    setCommandHistory(prev => [...prev, command]);
    setHistoryIndex(-1);

    if (command === 'clear') {
      terminal.clear();
      terminal.write('\x1b[32m$ \x1b[0m');
      setCursorX(0);
      setTimeout(() => lastCommandRef.current = null, 100);
      return;
    }

    if (command === 'help') {
      const helpText = [
        'Available commands:',
        '  python script.py    - Run Python script',
        '  pip install <pkg>   - Install Python package',
        '  ls                  - List files',
        '  cat <file>          - Show file contents',
        '  clear               - Clear terminal',
        '  help                - Show this help',
        '  pwd                 - Show current directory',
        ''
      ];
      helpText.forEach(line => terminal.writeln(line));
      terminal.write('\x1b[32m$ \x1b[0m');
      setCursorX(0);
      setTimeout(() => lastCommandRef.current = null, 100);
      return;
    }

    const success = sendTerminalCommand(command);

    if (!success) {
      terminal.write('\x1b[31mCommand failed to send\x1b[0m\r\n\x1b[32m$ \x1b[0m');
    }

    setCursorX(0);
    // Allow next command to be processed after a short delay
    setTimeout(() => lastCommandRef.current = null, 100);

  }, [sendTerminalCommand]);


  // Track the last processed line index to avoid duplicate processing
  const lastProcessedLineRef = useRef(0);

  // Handle terminal output from WebSocket
  useEffect(() => {
    console.log('🔍 [Terminal] useEffect triggered, terminalLines count:', state.terminalLines.length);
    const terminal = xtermRef.current;
    if (!terminal || !state.terminalLines.length) {
      console.log('🔍 [Terminal] Early return - terminal:', !!terminal, 'terminalLines:', state.terminalLines.length);
      return;
    }

    // Process only new lines since the last processed index
    const newLines = state.terminalLines.slice(lastProcessedLineRef.current);
    console.log('🔍 [Terminal] Processing', newLines.length, 'new lines');
    
    newLines.forEach((line, _index) => {
      console.log('🔍 [Terminal] Processing line:', line);
      if (line.type === 'input') {
        // Don't show input lines in terminal output - they're already shown when typed
        return;
      }
      
      if (line.type === 'output' || line.type === 'error') {
        // Handle special clear terminal command
        if (line.content === 'CLEAR_TERMINAL') {
          terminal.clear();
          terminal.write('\x1b[32m$ \x1b[0m');
          return;
        }
        
        // Write the command output (backend no longer includes command)
        if (line.content) {
          // Handle different line types with proper formatting
          if (line.type === 'error') {
            const formattedError = line.content.replace(/\n/g, '\r\n'); // Convert \n to \r\n
            terminal.write(`\x1b[31m${formattedError}\x1b[0m`); // Red for errors
          } else {
            // Write the command output, converting \n to proper terminal newlines
            const formattedContent = line.content.replace(/\n/g, '\r\n'); // Convert all \n to \r\n
            if (formattedContent) {
              terminal.write(formattedContent);
            }
          }
        }
        
        // Add newline and prompt after output
        terminal.write('\r\n\x1b[32m$ \x1b[0m');
        
        // Ensure terminal scrolls to bottom
        terminal.scrollToBottom();
      }
    });

    // Update the last processed line index
    lastProcessedLineRef.current = state.terminalLines.length;
  }, [state.terminalLines]);

  // Fit terminal when container resizes
  useEffect(() => {
    const resizeObserver = new ResizeObserver(() => {
      if (fitAddonRef.current) {
        setTimeout(() => {
          fitAddonRef.current?.fit();
        }, 0);
      }
    });

    if (terminalRef.current) {
      resizeObserver.observe(terminalRef.current);
    }

    return () => resizeObserver.disconnect();
  }, []);

  return (
    <div className="h-full flex flex-col bg-black">
      {/* Connection Status Header */}
      <div className="bg-gray-900 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
          <span className="text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'} 
            {state.currentSession && (
              <span className="text-gray-500 ml-2">
                Session: {state.currentSession.id.substring(0, 8)}...
              </span>
            )}
          </span>
        </div>
        <div className="text-xs text-gray-500">
          Terminal - Isolated Python 3.11+ Environment
        </div>
      </div>
      
      {/* Terminal Content */}
      <div 
        ref={terminalRef} 
        className="flex-1 p-2"
        style={{ minHeight: '200px' }}
        onClick={() => {
          if (xtermRef.current) {
            xtermRef.current.focus();
            console.log('🖱️ [Terminal] Terminal clicked and focused');
          }
        }}
      />
    </div>
  );
}