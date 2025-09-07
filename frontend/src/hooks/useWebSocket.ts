'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';

interface WebSocketMessage {
  type: 'terminal_input' | 'terminal_output' | 'code_execution' | 'file_system' | 'error';
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
}

export function useWebSocket() {
  const { state, setConnected, addTerminalLine, setError } = useApp();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        addTerminalLine('Connected to server', 'output');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          addTerminalLine('Error: Invalid message from server', 'error');
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnected(false);
        
        if (!event.wasClean && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          addTerminalLine(`Connection lost. Reconnecting in ${delay/1000}s...`, 'error');
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else {
          addTerminalLine('Disconnected from server', 'error');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        addTerminalLine('Connection error occurred', 'error');
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setError('Failed to connect to server');
      addTerminalLine('Failed to connect to server', 'error');
    }
  }, [setConnected, addTerminalLine, setError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    
    setConnected(false);
  }, [setConnected]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } else {
      addTerminalLine('Error: Not connected to server', 'error');
      return false;
    }
  }, [addTerminalLine]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('Received WebSocket message:', message);

    switch (message.type) {
      case 'terminal_output':
        if (message.output) {
          addTerminalLine(message.output, 'output');
        }
        break;

      case 'error':
        if (message.message) {
          addTerminalLine(`Error: ${message.message}`, 'error');
        }
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [addTerminalLine]);

  // WebSocket actions
  const sendTerminalCommand = useCallback((command: string) => {
    const success = sendMessage({
      type: 'terminal_input',
      sessionId: state.currentSession?.id || 'default',
      command
    });

    if (success) {
      addTerminalLine(`$ ${command}`, 'input');
    }

    return success;
  }, [sendMessage, state.currentSession?.id, addTerminalLine]);

  const executeCode = useCallback((code: string, filename?: string) => {
    return sendMessage({
      type: 'code_execution',
      sessionId: state.currentSession?.id || 'default',
      code,
      filename
    });
  }, [sendMessage, state.currentSession?.id]);

  const performFileOperation = useCallback((action: string, path: string, content?: string) => {
    return sendMessage({
      type: 'file_system',
      action,
      path,
      content
    });
  }, [sendMessage]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected: state.isConnected,
    connect,
    disconnect,
    sendTerminalCommand,
    executeCode,
    performFileOperation,
    sendMessage
  };
}