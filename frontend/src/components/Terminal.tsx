'use client';

import type { JSX } from 'react';
import { useCallback, useRef, useEffect, useState } from 'react';
import { useApp } from '../contexts/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Terminal as XTermTerminal } from '@xterm/xterm';
import type { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

interface TerminalProps {
  readOnly?: boolean;
}

export function Terminal({ readOnly = false }: TerminalProps): JSX.Element {
  const { state } = useApp();
  const { sendTerminalCommand } = useWebSocket();

  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTermTerminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [, setCurrentLine] = useState('');
  const currentLineRef = useRef('');
  const cursorPositionRef = useRef(0); // Track cursor position within the line
  const commandHistoryRef = useRef<string[]>([]);
  const historyIndexRef = useRef(-1);
  const lastProcessedLineRef = useRef(0);
  const isInitializedRef = useRef(false);
  const progressLineCountRef = useRef(0);

  const displayWelcomeMessage = useCallback((terminal: XTermTerminal) => {
    terminal.writeln('\x1b[36m╭────────────────────────────────────╮\x1b[0m');
    terminal.writeln('\x1b[36m│     Welcome to the Terminal       │\x1b[0m');
    terminal.writeln('\x1b[36m│ Type commands or "help" to begin  │\x1b[0m');
    terminal.writeln('\x1b[36m╰────────────────────────────────────╯\x1b[0m');
    terminal.write('\r\n\x1b[32m$ \x1b[0m');
  }, []);

  const replaceCurrentLine = useCallback((newLine: string, cursorPos?: number): void => {
    const terminal = xtermRef.current;
    if (!terminal) return;

    // Clear current line and rewrite
    terminal.write('\r\x1b[32m$ \x1b[0m');
    terminal.write(' '.repeat(currentLineRef.current.length));
    terminal.write('\r\x1b[32m$ \x1b[0m');
    terminal.write(newLine);

    // If cursor position is specified, move cursor to that position
    if (cursorPos !== undefined && cursorPos < newLine.length) {
      const moveBack = newLine.length - cursorPos;
      if (moveBack > 0) {
        terminal.write(`\x1b[${moveBack}D`); // Move cursor left
      }
    }
  }, []);

  const handleCommand = useCallback((command: string): void => {
    const terminal = xtermRef.current;
    if (!terminal) return;

    terminal.write('\r\n');

    if (!command.trim()) {
      terminal.write('\x1b[32m$ \x1b[0m');
      cursorPositionRef.current = 0;
      return;
    }

    commandHistoryRef.current = [...commandHistoryRef.current, command];
    historyIndexRef.current = -1;

    if (command === 'clear') {
      terminal.clear();
      terminal.write('\x1b[32m$ \x1b[0m');
      cursorPositionRef.current = 0;
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
      cursorPositionRef.current = 0;
      return;
    }

    const success = sendTerminalCommand(command);
    if (!success) {
      terminal.write('\x1b[31mCommand failed to send\x1b[0m\r\n\x1b[32m$ \x1b[0m');
    }
    cursorPositionRef.current = 0;
    // No fallback timeout - let the output handler deal with the prompt
  }, [sendTerminalCommand]);

  // Initialize terminal once
  useEffect(() => {
    if (isInitializedRef.current || !terminalRef.current) return;
    
    let mounted = true;
    
    const initTerminal = async () => {
      try {
        const [{ Terminal: XTerm }, { FitAddon }, { WebLinksAddon }] = await Promise.all([
          import('@xterm/xterm'),
          import('@xterm/addon-fit'),
          import('@xterm/addon-web-links'),
        ]);

        if (!mounted || !terminalRef.current) return;

        const terminal = new XTerm({
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
          if (readOnly) {
            return;
          }

          // Enter key
          if (data === '\r') {
            const cmd = currentLineRef.current.trim();
            currentLineRef.current = '';
            cursorPositionRef.current = 0;
            setCurrentLine('');
            handleCommand(cmd);
            return;
          }

          // Backspace/Delete
          if (data === '\u007F' || data === '\b' || data === '\u0008') {
            if (cursorPositionRef.current > 0) {
              const line = currentLineRef.current;
              const pos = cursorPositionRef.current;
              currentLineRef.current = line.slice(0, pos - 1) + line.slice(pos);
              cursorPositionRef.current = pos - 1;
              setCurrentLine(currentLineRef.current);
              replaceCurrentLine(currentLineRef.current, cursorPositionRef.current);
            }
            return;
          }

          // Up arrow - command history
          if (data === '\u001b[A') {
            if (commandHistoryRef.current.length > 0) {
              const newIndex = Math.min(historyIndexRef.current + 1, commandHistoryRef.current.length - 1);
              if (newIndex !== historyIndexRef.current) {
                historyIndexRef.current = newIndex;
                const cmd = commandHistoryRef.current[commandHistoryRef.current.length - 1 - newIndex] ?? '';
                currentLineRef.current = cmd;
                cursorPositionRef.current = cmd.length;
                replaceCurrentLine(cmd);
                setCurrentLine(cmd);
              }
            }
            return;
          }

          // Down arrow - command history
          if (data === '\u001b[B') {
            if (historyIndexRef.current >= 0) {
              const newIndex = historyIndexRef.current - 1;
              historyIndexRef.current = newIndex;
              const cmd = newIndex >= 0 ?
                commandHistoryRef.current[commandHistoryRef.current.length - 1 - newIndex] ?? '' : '';
              currentLineRef.current = cmd;
              cursorPositionRef.current = cmd.length;
              replaceCurrentLine(cmd);
              setCurrentLine(cmd);
            }
            return;
          }

          // Left arrow - move cursor left
          if (data === '\u001b[D') {
            if (cursorPositionRef.current > 0) {
              cursorPositionRef.current--;
              terminal.write('\x1b[D');
            }
            return;
          }

          // Right arrow - move cursor right
          if (data === '\u001b[C') {
            if (cursorPositionRef.current < currentLineRef.current.length) {
              cursorPositionRef.current++;
              terminal.write('\x1b[C');
            }
            return;
          }

          // Home key (Cmd+Left on Mac) - jump to beginning
          if (data === '\u001b[H' || data === '\u001bOH' || data === '\u001b[1~') {
            if (cursorPositionRef.current > 0) {
              terminal.write(`\x1b[${cursorPositionRef.current}D`);
              cursorPositionRef.current = 0;
            }
            return;
          }

          // End key (Cmd+Right on Mac) - jump to end
          if (data === '\u001b[F' || data === '\u001bOF' || data === '\u001b[4~') {
            const moveForward = currentLineRef.current.length - cursorPositionRef.current;
            if (moveForward > 0) {
              terminal.write(`\x1b[${moveForward}C`);
              cursorPositionRef.current = currentLineRef.current.length;
            }
            return;
          }

          // Option+Left (backward word) - jump to previous word
          if (data === '\u001bb' || data === '\u001b[1;3D') {
            const line = currentLineRef.current;
            const pos = cursorPositionRef.current;
            if (pos > 0) {
              let newPos = pos - 1;
              // Skip current whitespace
              while (newPos > 0 && line[newPos] === ' ') newPos--;
              // Skip to start of word
              while (newPos > 0 && line[newPos - 1] !== ' ') newPos--;
              const moveBack = pos - newPos;
              if (moveBack > 0) {
                terminal.write(`\x1b[${moveBack}D`);
                cursorPositionRef.current = newPos;
              }
            }
            return;
          }

          // Option+Right (forward word) - jump to next word
          if (data === '\u001bf' || data === '\u001b[1;3C') {
            const line = currentLineRef.current;
            const pos = cursorPositionRef.current;
            if (pos < line.length) {
              let newPos = pos;
              // Skip current whitespace
              while (newPos < line.length && line[newPos] === ' ') newPos++;
              // Skip to end of word
              while (newPos < line.length && line[newPos] !== ' ') newPos++;
              const moveForward = newPos - pos;
              if (moveForward > 0) {
                terminal.write(`\x1b[${moveForward}C`);
                cursorPositionRef.current = newPos;
              }
            }
            return;
          }

          // Ctrl+C - cancel current line
          if (data === '\u0003') {
            terminal.write('^C\r\n$ ');
            currentLineRef.current = '';
            cursorPositionRef.current = 0;
            setCurrentLine('');
            return;
          }

          // Ctrl+A - jump to beginning
          if (data === '\u0001') {
            if (cursorPositionRef.current > 0) {
              terminal.write(`\x1b[${cursorPositionRef.current}D`);
              cursorPositionRef.current = 0;
            }
            return;
          }

          // Ctrl+E - jump to end
          if (data === '\u0005') {
            const moveForward = currentLineRef.current.length - cursorPositionRef.current;
            if (moveForward > 0) {
              terminal.write(`\x1b[${moveForward}C`);
              cursorPositionRef.current = currentLineRef.current.length;
            }
            return;
          }

          // Tab and printable characters
          if (data >= ' ' || data === '\t') {
            const line = currentLineRef.current;
            const pos = cursorPositionRef.current;
            currentLineRef.current = line.slice(0, pos) + data + line.slice(pos);
            cursorPositionRef.current = pos + data.length;
            setCurrentLine(currentLineRef.current);

            // Optimize: if typing at end, just write the character directly
            if (pos === line.length) {
              terminal.write(data);
            } else {
              // Inserting in middle - need to rewrite the line
              replaceCurrentLine(currentLineRef.current, cursorPositionRef.current);
            }
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

    initTerminal().catch((error) => {
      console.error('Failed to start terminal:', error);
    });

    return () => {
      mounted = false;
    };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle terminal output
  useEffect(() => {
    const terminal = xtermRef.current;
    if (!terminal || !state.terminalLines.length) return;

    const newLines = state.terminalLines.slice(lastProcessedLineRef.current);

    newLines.forEach((line) => {
      // Display input lines (e.g., from Run Code button)
      if (line.type === 'input') {
        terminal.write(`${line.content}\r\n`);
        return;
      }

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
            if (output) {
              // If there's output, write it followed by newline and prompt
              terminal.write(output);
              terminal.write('\r\n\x1b[32m$ \x1b[0m');
            } else {
              // If no output, just write prompt (already on new line from handleCommand)
              terminal.write('\x1b[32m$ \x1b[0m');
            }
          }
        }
      }
    });

    lastProcessedLineRef.current = state.terminalLines.length;
  }, [state.terminalLines, displayWelcomeMessage]);

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