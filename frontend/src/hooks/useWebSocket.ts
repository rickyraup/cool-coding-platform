'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';

// Global WebSocket singleton to prevent multiple instances
let globalWebSocket: WebSocket | null = null;
let globalReconnectTimeout: NodeJS.Timeout | null = null;
let globalConnectionState = {
  isConnecting: false,
  connectionCount: 0,
  lastConnectionAttempt: 0,
  cooldownPeriod: 1000, // 1 second cooldown between connection attempts
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  hasEverConnected: false // Track if we've ever successfully connected
};

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
  // Use global WebSocket instead of local refs to prevent multiple instances
  const wsRef = useRef<WebSocket | null>(globalWebSocket);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(globalReconnectTimeout);
  const reconnectAttempts = useRef(globalConnectionState.reconnectAttempts);
  const maxReconnectAttempts = globalConnectionState.maxReconnectAttempts;
  const isConnectingRef = useRef(globalConnectionState.isConnecting);

  const connect = useCallback(() => {
    const now = Date.now();
    const timeSinceLastAttempt = now - globalConnectionState.lastConnectionAttempt;
    
    // Prevent multiple simultaneous connection attempts using global state
    if (globalWebSocket?.readyState === WebSocket.OPEN || 
        globalWebSocket?.readyState === WebSocket.CONNECTING ||
        globalConnectionState.isConnecting) {
      return;
    }

    // Prevent rapid connection attempts with cooldown
    if (timeSinceLastAttempt < globalConnectionState.cooldownPeriod) {
      return;
    }

    // Clean up any existing connection
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      wsRef.current.close();
    }

    try {
      isConnectingRef.current = true;
      globalConnectionState.isConnecting = true;
      globalConnectionState.lastConnectionAttempt = now;
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws';
      console.log('🔌 [WS] Connecting to:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('✅ [WS] WebSocket connected successfully');
        isConnectingRef.current = false;
        globalConnectionState.isConnecting = false;
        globalConnectionState.hasEverConnected = true; // Mark that we've connected at least once
        setConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        // Don't add connection messages to terminal - show in status header only
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
        console.log('❌ [WS] WebSocket closed - Code:', event.code, 'WasClean:', event.wasClean);
        isConnectingRef.current = false;
        globalConnectionState.isConnecting = false;
        setConnected(false);
        
        // Only attempt reconnection for non-clean disconnects and if under max attempts
        const shouldReconnect = !event.wasClean && reconnectAttempts.current < maxReconnectAttempts && globalConnectionState.hasEverConnected;
        
        if (shouldReconnect) {
          reconnectAttempts.current++;
          const delay = Math.min(2000 * reconnectAttempts.current, 10000);
          console.log(`⏰ [WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (event.wasClean) {
          // Clean disconnect, don't show error
          console.log('🚫 [WS] Clean disconnect');
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.log('🚫 [WS] Max reconnection attempts reached');
          setError('Connection lost - please refresh page');
        } else if (!globalConnectionState.hasEverConnected) {
          // Never connected, likely server is down
          console.log('🚫 [WS] Unable to establish initial connection');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('💥 [WS] WebSocket error:', error);
        console.log('🔧 [WS] Setting state: isConnecting=false');
        isConnectingRef.current = false;
        globalConnectionState.isConnecting = false;
        setError('WebSocket connection error');
        addTerminalLine('Connection error occurred', 'error');
      };

    } catch (error) {
      console.error('💥 [WS] Failed to create WebSocket connection:', error);
      console.log('🔧 [WS] Setting state: isConnecting=false');
      isConnectingRef.current = false;
      globalConnectionState.isConnecting = false;
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
    globalConnectionState.isConnecting = false;
    reconnectAttempts.current = 0;
    lastSessionIdRef.current = null; // Reset session tracking on disconnect
    
    if (wsRef.current) {
      console.log('🔌 [WS] Closing WebSocket with code 1000');
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    
    setConnected(false);
  }, [setConnected]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    console.log('🚀 [WS] Attempting to send message:', message);
    console.log('🔌 [WS] WebSocket ref:', wsRef.current);
    console.log('🔌 [WS] WebSocket state:', wsRef.current?.readyState, 'OPEN=', WebSocket.OPEN);
    console.log('🔌 [WS] Connected state:', state.isConnected);
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('✅ [WS] Sending message via WebSocket');
      wsRef.current.send(JSON.stringify(message));
      return true;
    } else {
      console.log('❌ [WS] WebSocket not ready - ref:', !!wsRef.current, 'state:', wsRef.current?.readyState, 'connected:', state.isConnected);
      
      // Try to reconnect if WebSocket ref is null or closed
      if (!wsRef.current && !isConnectingRef.current) {
        console.log('🔄 [WS] WebSocket ref is null, attempting to reconnect...');
        connect();
      }
      
      // Don't add error messages to terminal - connection status shown in header
      return false;
    }
  }, [connect]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('Received WebSocket message:', message);

    switch (message.type) {
      case 'connection_established':
        console.log('WebSocket connection confirmed:', message.message);
        // Don't add connection messages to terminal - show in status header only
        break;

      case 'terminal_output':
        if (message.output) {
          addTerminalLine(message.output, 'output');
        }
        break;

      case 'terminal_clear':
        // Clear terminal - this will be handled by the Terminal component
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

      case 'file_system':
        // Handle file system responses
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
        console.log('Unknown message type:', message.type);
    }
  }, [addTerminalLine, setFiles, updateCode]);

  // WebSocket actions
  const sendTerminalCommand = useCallback((command: string) => {
    console.log('🎯 [WS] sendTerminalCommand called with:', command);
    console.log('🎯 [WS] Current session ID:', state.currentSession?.id);
    
    const success = sendMessage({
      type: 'terminal_input',
      sessionId: state.currentSession?.id || 'default',
      command
    });

    console.log('🎯 [WS] sendMessage returned:', success);

    // Don't add the command to terminal lines here - let the terminal component handle display
    // The actual output will come back via WebSocket message

    return success;
  }, [sendMessage, state.currentSession?.id]);

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

  // Track the last session ID to prevent duplicate messages
  const lastSessionIdRef = useRef<string | null>(null);

  // Monitor session changes and refresh files
  useEffect(() => {
    if (state.isConnected && state.currentSession && state.currentSession.id !== lastSessionIdRef.current) {
      console.log('🔄 [WS] Session changed, refreshing files for session:', state.currentSession.id);
      lastSessionIdRef.current = state.currentSession.id;
      
      // Small delay to ensure session is fully set up
      const refreshTimeout = setTimeout(() => {
        performFileOperation('list', '');
        addTerminalLine(`🔄 Switched to session: ${state.currentSession?.id.substring(0, 8)}...`, 'output');
      }, 200);
      
      return () => clearTimeout(refreshTimeout);
    }
  }, [state.currentSession?.id, state.isConnected, performFileOperation]);

  // Only connect from the first hook instance (prevent multiple connections)
  useEffect(() => {
    globalConnectionState.connectionCount++;
    console.log('🚀 [WS] useWebSocket hook mounted, connection count:', globalConnectionState.connectionCount);
    
    // Only the first instance should connect
    if (globalConnectionState.connectionCount === 1) {
      console.log('🎯 [WS] First hook instance - initiating connection');
      const connectTimeout = setTimeout(() => {
        connect();
      }, 100);
      
      return () => {
        console.log('🧹 [WS] First hook instance unmounting - disconnecting');
        clearTimeout(connectTimeout);
        globalConnectionState.connectionCount--;
        disconnect();
      };
    } else {
      console.log('🔗 [WS] Additional hook instance - sharing existing connection');
      return () => {
        globalConnectionState.connectionCount--;
        console.log('🔗 [WS] Additional hook instance unmounting, connection count:', globalConnectionState.connectionCount);
      };
    }
  }, []);

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