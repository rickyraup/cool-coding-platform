'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';

interface WebSocketMessage {
  type: 'terminal_input' | 'terminal_output' | 'code_execution' | 'file_system' | 'error' | 'connection_established' | 'file_list';
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
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const isConnectingRef = useRef(false);

  const connect = useCallback(() => {
    console.log('🔄 [WS] Connect called, current state:', {
      readyState: wsRef.current?.readyState,
      isConnecting: isConnectingRef.current,
      reconnectAttempts: reconnectAttempts.current
    });

    // Prevent multiple simultaneous connection attempts
    if (wsRef.current?.readyState === WebSocket.OPEN || isConnectingRef.current) {
      console.log('🛑 [WS] Already connected or connecting, skipping');
      return;
    }

    // Clean up any existing connection
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('🧹 [WS] Cleaning up existing CONNECTING websocket');
      wsRef.current.close();
    }

    try {
      isConnectingRef.current = true;
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws';
      console.log('🔌 [WS] Attempting WebSocket connection to:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);
      console.log('📞 [WS] WebSocket instance created, readyState:', wsRef.current.readyState);

      wsRef.current.onopen = () => {
        console.log('✅ [WS] WebSocket connected successfully');
        console.log('🔧 [WS] Setting state: isConnecting=false, connected=true, reconnectAttempts=0');
        isConnectingRef.current = false;
        setConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        addTerminalLine('Connected to server', 'output');
      };

      wsRef.current.onmessage = (event) => {
        console.log('📥 [WS] Received message:', event.data);
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📋 [WS] Parsed message:', message);
          handleMessage(message);
        } catch (error) {
          console.error('❌ [WS] Failed to parse WebSocket message:', error);
          addTerminalLine('Error: Invalid message from server', 'error');
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('❌ [WS] WebSocket closed - Code:', event.code, 'Reason:', event.reason, 'WasClean:', event.wasClean);
        console.log('🔧 [WS] Setting state: isConnecting=false, connected=false');
        isConnectingRef.current = false;
        setConnected(false);
        
        // Only attempt reconnection for specific error codes and if under max attempts
        const shouldReconnect = !event.wasClean && reconnectAttempts.current < maxReconnectAttempts && event.code !== 1006;
        console.log('🤔 [WS] Should reconnect?', {
          wasClean: event.wasClean,
          reconnectAttempts: reconnectAttempts.current,
          maxAttempts: maxReconnectAttempts,
          code: event.code,
          shouldReconnect
        });

        if (shouldReconnect) {
          reconnectAttempts.current++;
          const delay = Math.min(2000 * reconnectAttempts.current, 10000); // Longer delays
          console.log(`⏰ [WS] Scheduling reconnect attempt ${reconnectAttempts.current}/${maxReconnectAttempts} in ${delay}ms`);
          addTerminalLine(`Connection lost. Reconnecting in ${delay/1000}s... (${reconnectAttempts.current}/${maxReconnectAttempts})`, 'error');
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 [WS] Executing scheduled reconnect');
            connect();
          }, delay);
        } else {
          console.log('🚫 [WS] Not attempting reconnection - max attempts reached or clean disconnect');
          addTerminalLine('Disconnected from server', 'error');
          if (reconnectAttempts.current >= maxReconnectAttempts) {
            setError('Maximum reconnection attempts reached');
          }
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('💥 [WS] WebSocket error:', error);
        console.log('🔧 [WS] Setting state: isConnecting=false');
        isConnectingRef.current = false;
        setError('WebSocket connection error');
        addTerminalLine('Connection error occurred', 'error');
      };

    } catch (error) {
      console.error('💥 [WS] Failed to create WebSocket connection:', error);
      console.log('🔧 [WS] Setting state: isConnecting=false');
      isConnectingRef.current = false;
      setError('Failed to connect to server');
      addTerminalLine('Failed to connect to server', 'error');
    }
  }, [setConnected, addTerminalLine, setError]);

  const disconnect = useCallback(() => {
    console.log('🔌 [WS] Disconnect called');
    if (reconnectTimeoutRef.current) {
      console.log('⏰ [WS] Clearing reconnect timeout');
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    console.log('🔧 [WS] Setting state: isConnecting=false, reconnectAttempts=0');
    isConnectingRef.current = false;
    reconnectAttempts.current = 0;
    
    if (wsRef.current) {
      console.log('🔌 [WS] Closing WebSocket with code 1000');
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
      case 'connection_established':
        console.log('WebSocket connection confirmed:', message.message);
        addTerminalLine('Connected to Code Execution Platform', 'output');
        break;

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

      case 'file_list':
        if (message.files) {
          setFiles(message.files);
        }
        break;

      case 'file_system':
        // Handle file system responses
        if (message.action === 'read' && message.content) {
          updateCode(message.content);
        } else if (message.action === 'list' && message.files) {
          setFiles(message.files);
        }
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [addTerminalLine, setFiles, updateCode]);

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
    console.log('🚀 [WS] useWebSocket hook mounted, calling connect');
    connect();
    
    return () => {
      console.log('🧹 [WS] useWebSocket hook unmounting, calling disconnect');
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