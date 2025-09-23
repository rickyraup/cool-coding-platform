'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';

// Global WebSocket singleton with proper cleanup
class WebSocketManager {
  private ws: WebSocket | null = null;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private readonly messageHandlers: Set<(message: WebSocketMessage) => void> = new Set();
  private readonly connectionStateHandlers: Set<(connected: boolean) => void> = new Set();
  private readonly handlerIds: Map<Function, string> = new Map(); // Track unique handlers

  constructor() {
    // Ensure cleanup on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.disconnect());
    }
  }

  addMessageHandler(handler: (message: WebSocketMessage) => void, id?: string) {
    // Clear all existing handlers first to prevent duplicates from React Strict Mode
    if (id === 'main-handler') {
      this.messageHandlers.clear();
      this.handlerIds.clear();
    }
    
    const handlerId = id || `handler_${Date.now()}_${Math.random()}`;
    this.handlerIds.set(handler, handlerId);
    this.messageHandlers.add(handler);
  }

  removeMessageHandler(handler: (message: WebSocketMessage) => void) {
    this.handlerIds.delete(handler);
    this.messageHandlers.delete(handler);
  }

  addConnectionStateHandler(handler: (connected: boolean) => void, id?: string) {
    // Clear all existing connection handlers for main registration
    if (id === 'main-connection') {
      this.connectionStateHandlers.clear();
    }
    
    this.connectionStateHandlers.add(handler);
  }

  removeConnectionStateHandler(handler: (connected: boolean) => void) {
    this.connectionStateHandlers.delete(handler);
  }

  private notifyConnectionState(connected: boolean) {
    this.connectionStateHandlers.forEach(handler => handler(connected));
  }

  private notifyMessage(message: WebSocketMessage) {
    this.messageHandlers.forEach(handler => handler(message));
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket('ws://localhost:8001/ws');

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.notifyConnectionState(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.notifyMessage(message);
        } catch {
          // Ignore parse errors
        }
      };

      this.ws.onclose = (event) => {
        this.isConnecting = false;
        this.notifyConnectionState(false);

        // Reconnect if unexpected close
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = Math.min(1000 * this.reconnectAttempts, 5000);
          this.reconnectTimeout = setTimeout(() => this.connect(), delay);
        }
      };

      this.ws.onerror = () => {
        this.isConnecting = false;
      };
    } catch {
      this.isConnecting = false;
    }
  }

  sendMessage(message: WebSocketMessage): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch {
        return false;
      }
    } else {
      if (!this.isConnecting) {
        this.connect();
      }
      return false;
    }
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.notifyConnectionState(false);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN || false;
  }
}

// Global singleton instance with forced reset capability
let wsManager: WebSocketManager;

// Function to ensure we have a clean singleton
function getWebSocketManager(): WebSocketManager {
  if (!wsManager) {
    wsManager = new WebSocketManager();
  }
  return wsManager;
}

interface WebSocketMessage {
  type: 'terminal_input' | 'terminal_output' | 'terminal_clear' | 'code_execution' | 'file_system' | 'error' | 'connection_established' | 'file_list' | 'file_input_prompt' | 'file_input_response' | 'file_created' | 'ping' | 'pong';
  sessionId?: string;
  command?: string;
  output?: string;
  timestamp?: string;
  code?: string;
  filename?: string;
  action?: string;
  path?: string;
  content?: string;
  message?: string;
  files?: { name: string; type: 'file' | 'directory'; path: string; }[];
}

export function useWebSocket() {
  const { state, setConnected, addTerminalLine, setError, setFiles, updateCode } = useApp();

  // Create stable handler refs to prevent duplicate registrations
  const handlersRegisteredRef = useRef(false);

  // Register handlers only once using refs
  useEffect(() => {
    if (handlersRegisteredRef.current) return;
    
    const handleMessage = (message: WebSocketMessage) => {
      switch (message.type) {
        case 'connection_established':
          break;

        case 'terminal_output':
          if (message.output) {
            addTerminalLine(message.output, 'output', message.command);
          }
          break;

        case 'terminal_clear':
          addTerminalLine('CLEAR_TERMINAL', 'output');
          break;

        case 'error':
          if (message.message) {
            addTerminalLine(`Error: ${message.message}`, 'error');
          }
          break;

        case 'file_list':
          if (message.files) {
            setFiles(message.files);
          }
          break;

        case 'file_input_prompt':
          if (message.filename) {
            addTerminalLine(message.message || `Enter content for ${message.filename}:`, 'output');
          }
          break;

        case 'ping':
          getWebSocketManager().sendMessage({ type: 'pong' });
          break;

        case 'file_created':
          if (message.files) {
            setFiles(message.files);
          }
          if (message.message) {
            addTerminalLine(message.message, 'output');
          }
          break;

        case 'file_system':
          if (message.action === 'read' && message.content) {
            updateCode(message.content);
          } else if (message.action === 'list' && message.files) {
            setFiles(message.files);
          } else if (message.action === 'file_created' && message.files) {
            setFiles(message.files);
            addTerminalLine(`File created: ${message.path}`, 'output');
          } else if (message.action === 'directory_created' && message.files) {
            setFiles(message.files);
            addTerminalLine(`Directory created: ${message.path}`, 'output');
          } else if (message.action === 'deleted' && message.files) {
            setFiles(message.files);
            addTerminalLine(`Deleted: ${message.path}`, 'output');
          }
          break;

        default:
          break;
      }
    };

    const handleConnectionState = (connected: boolean) => {
      setConnected(connected);
      if (!connected) {
        setError('Connection lost');
      } else {
        setError(null);
      }
    };

    const manager = getWebSocketManager();
    manager.addMessageHandler(handleMessage, 'main-handler');
    manager.addConnectionStateHandler(handleConnectionState, 'main-connection');
    handlersRegisteredRef.current = true;
    
    return () => {
      manager.removeMessageHandler(handleMessage);
      manager.removeConnectionStateHandler(handleConnectionState);
      handlersRegisteredRef.current = false;
    };
  }, []); // Empty dependency array - register only once

  // Connect when session is available
  useEffect(() => {
    if (state.currentSession) {
      getWebSocketManager().connect();
    }
  }, [state.currentSession?.id]);

  // Session change handling
  const handledSessionIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (
      getWebSocketManager().isConnected() && 
      state.currentSession && 
      state.currentSession.id !== handledSessionIdRef.current
    ) {
      handledSessionIdRef.current = state.currentSession.id;
      
      const refreshTimeout = setTimeout(() => {
        performFileOperation('list', '');
        addTerminalLine(`🔄 Switched to session: ${state.currentSession?.id.substring(0, 8)}...`, 'output');
      }, 50); // Reduced from 200ms to 50ms for faster loading
      
      return () => clearTimeout(refreshTimeout);
    }
    // Return undefined cleanup function for the else case
    return undefined;
  }, [state.currentSession?.id, addTerminalLine]);

  // WebSocket actions using the manager
  const sendTerminalCommand = useCallback((command: string) => {
    return getWebSocketManager().sendMessage({
      type: 'terminal_input',
      sessionId: state.currentSession?.id || 'default',
      command
    });
  }, [state.currentSession?.id]);

  const executeCode = useCallback((code: string, filename?: string) => {
    return getWebSocketManager().sendMessage({
      type: 'code_execution',
      sessionId: state.currentSession?.id || 'default',
      code,
      ...(filename !== undefined && { filename })
    });
  }, [state.currentSession?.id]);

  const performFileOperation = useCallback((action: string, path: string, content?: string) => {
    return getWebSocketManager().sendMessage({
      type: 'file_system',
      sessionId: state.currentSession?.id || 'default',
      action,
      path,
      ...(content !== undefined && { content })
    });
  }, [state.currentSession?.id]);

  const saveCurrentFile = useCallback((content: string, filename?: string) => {
    const currentFile = filename || state.currentFile || 'main.py';
    return performFileOperation('write', currentFile, content);
  }, [performFileOperation, state.currentFile]);

  const sendFileInputResponse = useCallback((filename: string, content: string) => {
    return getWebSocketManager().sendMessage({
      type: 'file_input_response',
      sessionId: state.currentSession?.id || 'default',
      filename,
      content
    });
  }, [state.currentSession?.id]);

  const manager = getWebSocketManager();
  return {
    isConnected: manager.isConnected(),
    connect: () => manager.connect(),
    disconnect: () => manager.disconnect(),
    sendTerminalCommand,
    executeCode,
    performFileOperation,
    saveCurrentFile,
    sendFileInputResponse,
    sendMessage: manager.sendMessage.bind(manager)
  };
}