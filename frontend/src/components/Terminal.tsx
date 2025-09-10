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
          
          // Ensure terminal gets focus for keyboard input
          setTimeout(() => {
            terminal.focus();
            console.log('🎯 [Terminal] Terminal focused for keyboard input');
          }, 100);
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

          // Debug: log ALL key data
          console.log('🎹 [Terminal] onData received:', JSON.stringify(data), 'charCode:', data.charCodeAt(0));
          if (data.charCodeAt(0) <= 32 || data.includes('\u001b')) {
            console.log('🔑 [Terminal] Special key pressed:', data.charCodeAt(0), JSON.stringify(data));
          }

          // Handle special keys
          if (data === '\r') { // Enter key
            // Get current value from state using functional update
            setCurrentLine(currentCmd => {
              console.log('🔥 [Terminal] Enter pressed, currentLine:', JSON.stringify(currentCmd));
              handleCommand(currentCmd);
              return ''; // Clear the line
            });
            setCursorX(0);
            return;
          }
          
          if (data === '\u007F' || data === '\b' || data === '\u0008') { // Backspace (multiple variants)
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
            console.log('📝 [Terminal] Adding character to currentLine:', JSON.stringify(data), 'charCode:', data.charCodeAt(0));
            setCurrentLine(prev => {
              const newLine = prev + data;
              console.log('📝 [Terminal] Updated currentLine:', JSON.stringify(newLine));
              return newLine;
            });
            setCursorX(prev => prev + 1);
            terminal.write(data);
          } else {
            console.log('🚫 [Terminal] Character ignored:', JSON.stringify(data), 'charCode:', data.charCodeAt(0));
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
    console.log('🎯 [Terminal] handleCommand called with:', JSON.stringify(command));
    const terminal = xtermRef.current;
    if (!terminal) return;

    terminal.write('\r\n');
    
    if (!command.trim()) {
      terminal.write('$ ');
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
      setCursorX(0);
      return;
    }

    // Send command via WebSocket
    sendTerminalCommand(command);
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