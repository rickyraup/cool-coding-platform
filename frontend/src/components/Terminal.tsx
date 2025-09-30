'use client';

import type { JSX } from 'react';
import { useCallback, useRef, useEffect, useState } from 'react';
import { useApp } from '../contexts/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';
import '@xterm/xterm/css/xterm.css';

interface TerminalProps {
  readOnly?: boolean;
  reviewMode?: boolean;
}

export function Terminal({ readOnly = false, reviewMode = false }: TerminalProps): JSX.Element {
  const { state } = useApp();
  const { sendTerminalCommand } = useWebSocket();

  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);
  const [, setCurrentLine] = useState('');
  const currentLineRef = useRef('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const lastProcessedLineRef = useRef(0);
  const isInitializedRef = useRef(false);
  const progressLineCountRef = useRef(0);

  const displayWelcomeMessage = useCallback((terminal: any) => {
    if (reviewMode) {
      terminal.writeln('\x1b[36m╭────────────────────────────────────╮\x1b[0m');
      terminal.writeln('\x1b[36m│     Review Mode Terminal          │\x1b[0m');
      terminal.writeln('\x1b[36m│ Read-only: Use arrows to run files │\x1b[0m');
      terminal.writeln('\x1b[36m╰────────────────────────────────────╯\x1b[0m');
      terminal.writeln('');
    } else {
      terminal.writeln('\x1b[36m╭────────────────────────────────────╮\x1b[0m');
      terminal.writeln('\x1b[36m│     Welcome to the Terminal       │\x1b[0m');
      terminal.writeln('\x1b[36m│ Type commands or "help" to begin  │\x1b[0m');
      terminal.writeln('\x1b[36m╰────────────────────────────────────╯\x1b[0m');
      terminal.write('\r\n\x1b[32m$ \x1b[0m');
    }
  }, [reviewMode]);

  const replaceCurrentLine = useCallback((newLine: string): void => {
    const terminal = xtermRef.current;
    if (!terminal) return;
    terminal.write('\r\x1b[32m$ \x1b[0m');
    terminal.write(' '.repeat(currentLineRef.current.length));
    terminal.write('\r\x1b[32m$ \x1b[0m');
    terminal.write(newLine);
  }, []);

  const handleCommand = useCallback((command: string): void => {
    const terminal = xtermRef.current;
    if (!terminal) return;

    terminal.write('\r\n');

    if (!command.trim()) {
      terminal.write('\x1b[32m$ \x1b[0m');
      return;
    }

    setCommandHistory(prev => [...prev, command]);
    setHistoryIndex(-1);

    if (command === 'clear') {
      terminal.clear();
      terminal.write('\x1b[32m$ \x1b[0m');
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
      return;
    }

    const success = sendTerminalCommand(command);
    if (!success) {
      terminal.write('\x1b[31mCommand failed to send\x1b[0m\r\n\x1b[32m$ \x1b[0m');
    }
    // No fallback timeout - let the output handler deal with the prompt
  }, [sendTerminalCommand]);

  // Initialize terminal once
  useEffect(() => {
    if (isInitializedRef.current || !terminalRef.current) return;
    
    let mounted = true;
    
    const initTerminal = async () => {
      try {
        const [{ Terminal }, { FitAddon }, { WebLinksAddon }] = await Promise.all([
          import('@xterm/xterm'),
          import('@xterm/addon-fit'),
          import('@xterm/addon-web-links'),
        ]);

        if (!mounted || !terminalRef.current) return;

        const terminal = new Terminal({
          theme: {
            background: '#000000',
            foreground: '#ffffff',
            cursor: '#00ff00',
          },
          fontFamily: '"Courier New", Courier, monospace',
          fontSize: 14,
          cursorBlink: true,
          scrollback: 5000,
          convertEol: true,
        });

        const fitAddon = new FitAddon();
        const webLinksAddon = new WebLinksAddon();

        terminal.loadAddon(fitAddon);
        terminal.loadAddon(webLinksAddon);

        terminal.open(terminalRef.current);
        fitAddon.fit();

        xtermRef.current = terminal;
        fitAddonRef.current = fitAddon;
        isInitializedRef.current = true;

        displayWelcomeMessage(terminal);

        terminal.onData((data: string) => {
          // In read-only mode, ignore all input
          if (readOnly || reviewMode) {
            return;
          }

          if (data === '\r') {
            const cmd = currentLineRef.current.trim();
            currentLineRef.current = '';
            setCurrentLine('');
            handleCommand(cmd);
            return;
          }

          if (data === '\u007F' || data === '\b' || data === '\u0008') {
            if (currentLineRef.current.length > 0) {
              currentLineRef.current = currentLineRef.current.slice(0, -1);
              setCurrentLine(currentLineRef.current);
              replaceCurrentLine(currentLineRef.current);
            }
            return;
          }

          if (data === '\u001b[A') {
            if (commandHistory.length > 0) {
              const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1);
              if (newIndex !== historyIndex) {
                setHistoryIndex(newIndex);
                const cmd = commandHistory[commandHistory.length - 1 - newIndex] ?? '';
                currentLineRef.current = cmd;
                replaceCurrentLine(cmd);
                setCurrentLine(cmd);
              }
            }
            return;
          }

          if (data === '\u001b[B') {
            if (historyIndex >= 0) {
              const newIndex = historyIndex - 1;
              setHistoryIndex(newIndex);
              const cmd = newIndex >= 0 ?
                commandHistory[commandHistory.length - 1 - newIndex] ?? '' : '';
              currentLineRef.current = cmd;
              replaceCurrentLine(cmd);
              setCurrentLine(cmd);
            }
            return;
          }

          if (data === '\u0003') {
            terminal.write('^C\r\n$ ');
            currentLineRef.current = '';
            setCurrentLine('');
            return;
          }

          if (data >= ' ' || data === '\t') {
            currentLineRef.current = currentLineRef.current + data;
            setCurrentLine(currentLineRef.current);
            terminal.write(data);
          }
        });

        const handleResize = (): void => {
          fitAddonRef.current?.fit();
        };

        window.addEventListener('resize', handleResize);

        return () => {
          window.removeEventListener('resize', handleResize);
        };

      } catch (error) {
        console.error('Failed to initialize terminal:', error);
        return;
      }
    };

    initTerminal();

    return () => {
      mounted = false;
    };
  }, []); // Empty dependency array - only run once

  // Handle terminal output
  useEffect(() => {
    const terminal = xtermRef.current;
    if (!terminal || !state.terminalLines.length) return;

    const newLines = state.terminalLines.slice(lastProcessedLineRef.current);

    newLines.forEach((line) => {
      if (line.type === 'input') return;

      // Ignore pod_ready and clear_progress messages
      if (line.type === 'pod_ready' || line.type === 'clear_progress') {
        return;
      }

      if (line.type === 'output' || line.type === 'error') {
        if (line.content === 'CLEAR_TERMINAL') {
          terminal.clear();
          displayWelcomeMessage(terminal);
          progressLineCountRef.current = 0;
          return;
        }

        // Track progress messages (those starting with ⏳)
        if (line.content.trim().startsWith('⏳')) {
          // Progress messages overwrite the current line
          terminal.write('\r\x1b[2K' + line.content.trim());
          progressLineCountRef.current = 1;
        } else {
          // Regular output
          progressLineCountRef.current = 0;

          if (line.type === 'error') {
            terminal.write(`\x1b[31mError: ${line.content.trim()}\x1b[0m`);
            terminal.write('\r\n\x1b[32m$ \x1b[0m');
          } else {
            // Write the output (trimmed to remove trailing newlines)
            const output = line.content.trim();
            terminal.write(output);
            // Add newline and prompt after output
            terminal.write('\r\n\x1b[32m$ \x1b[0m');
          }
        }
      }
    });

    lastProcessedLineRef.current = state.terminalLines.length;
  }, [state.terminalLines]);

  // Handle resize
  useEffect(() => {
    const resizeObserver = new ResizeObserver(() => {
      // Immediate fitting for faster loading
      fitAddonRef.current?.fit();
    });

    if (terminalRef.current) {
      resizeObserver.observe(terminalRef.current);
    }

    return () => resizeObserver.disconnect();
  }, []);

  return (
    <div className="h-full relative">
      <div
        ref={terminalRef}
        className="rounded-lg border border-gray-800 bg-gray-900 shadow-lg"
        style={{ 
          width: '100%', 
          height: '100%', 
          minHeight: 300,
          overflow: 'hidden',
          position: 'relative',
          zIndex: 1
        }}
      />
    </div>
  );
}