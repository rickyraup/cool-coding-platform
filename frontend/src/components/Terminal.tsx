'use client';

import { useCallback, useRef, useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function Terminal(): JSX.Element {
  const { state, clearTerminal } = useApp();
  const { sendTerminalCommand } = useWebSocket();
  
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);
  const [currentLine, setCurrentLine] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [cursorX, setCursorX] = useState(0);

  // Initialize xterm
  useEffect(() => {
    if (typeof window === 'undefined' || !terminalRef.current || xtermRef.current) return;

    const initializeTerminal = async () => {
      try {
        // Dynamically import XTerm modules only on client side
        const [
          { Terminal },
          { FitAddon },
          { WebLinksAddon }
        ] = await Promise.all([
          import('@xterm/xterm'),
          import('@xterm/addon-fit'),
          import('@xterm/addon-web-links')
        ]);

        // Also import the CSS
        await import('@xterm/xterm/css/xterm.css');

        const terminal = new Terminal({
          theme: {
            background: '#000000',
            foreground: '#00ff00',
            cursor: '#00ff00',
            black: '#000000',
            red: '#ff5555',
            green: '#50fa7b',
            yellow: '#f1fa8c',
            blue: '#bd93f9',
            magenta: '#ff79c6',
            cyan: '#8be9fd',
            white: '#f8f8f2',
            brightBlack: '#6272a4',
            brightRed: '#ff6e6e',
            brightGreen: '#69ff94',
            brightYellow: '#ffffa5',
            brightBlue: '#d6acff',
            brightMagenta: '#ff92df',
            brightCyan: '#a4ffff',
            brightWhite: '#ffffff'
          },
          fontFamily: 'ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
          fontSize: 14,
          cursorBlink: true,
          cursorStyle: 'block',
          scrollback: 1000,
          tabStopWidth: 4,
        });

        const fitAddon = new FitAddon();
        const webLinksAddon = new WebLinksAddon();
        
        terminal.loadAddon(fitAddon);
        terminal.loadAddon(webLinksAddon);
        
        if (terminalRef.current) {
          terminal.open(terminalRef.current);
          fitAddon.fit();
        }
        
        // Welcome message
        terminal.writeln('\x1b[32mCode Execution Platform Terminal\x1b[0m');
        terminal.writeln('Type commands or "help" for available commands.');
        terminal.write('\r\n$ ');
        
        xtermRef.current = terminal;
        fitAddonRef.current = fitAddon;

        // Handle terminal input
        terminal.onData((data: string): void => {
          const terminal = xtermRef.current;
          if (!terminal) return;

          // Handle special keys
          if (data === '\r') { // Enter key
            handleCommand(currentLine);
            return;
          }
          
          if (data === '\u007F') { // Backspace
            if (cursorX > 0) {
              const newLine = currentLine.slice(0, -1);
              setCurrentLine(newLine);
              setCursorX(cursorX - 1);
              terminal.write('\b \b');
            }
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
          
          // Regular character input
          if (data >= ' ' || data === '\t') {
            setCurrentLine(prev => prev + data);
            setCursorX(prev => prev + 1);
            terminal.write(data);
          }
        });

        // Handle window resize
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

    // Clear current line
    terminal.write('\r$ ' + ' '.repeat(currentLine.length) + '\r$ ');
    
    // Write new line
    terminal.write(newLine);
    setCurrentLine(newLine);
    setCursorX(newLine.length);
  }, [currentLine]);

  const handleCommand = useCallback((command: string): void => {
    const terminal = xtermRef.current;
    if (!terminal) return;

    terminal.write('\r\n');
    
    if (!command.trim()) {
      terminal.write('$ ');
      setCurrentLine('');
      setCursorX(0);
      return;
    }

    // Add to history
    setCommandHistory(prev => [...prev, command]);
    setHistoryIndex(-1);

    // Handle local commands
    if (command === 'clear') {
      terminal.clear();
      terminal.write('$ ');
      setCurrentLine('');
      setCursorX(0);
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
      terminal.write('$ ');
      setCurrentLine('');
      setCursorX(0);
      return;
    }

    // Send command via WebSocket
    sendTerminalCommand(command);
    setCurrentLine('');
    setCursorX(0);
  }, [sendTerminalCommand]);

  // Handle terminal output from WebSocket
  useEffect(() => {
    const terminal = xtermRef.current;
    if (!terminal || !state.terminalLines.length) return;

    const lastLine = state.terminalLines[state.terminalLines.length - 1];
    if (!lastLine || lastLine.type === 'input') return;

    // Write output and prompt
    if (lastLine.content) {
      terminal.write(lastLine.content);
    }
    terminal.write('\r\n$ ');
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
      <div 
        ref={terminalRef} 
        className="flex-1 p-2"
        style={{ minHeight: '200px' }}
      />
    </div>
  );
}