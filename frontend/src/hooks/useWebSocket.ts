'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { usePathname } from 'next/navigation';
import { toast } from 'sonner';
import { useApp } from '../contexts/AppContext';

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

  connect(userId?: string) {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      // Add user authentication to WebSocket URL
      const WS_BASE_URL = process.env['NEXT_PUBLIC_WS_URL'] ?? 'ws://localhost:8002/ws';
      const wsUrl = userId
        ? `${WS_BASE_URL}?user_id=${encodeURIComponent(userId)}`
        : WS_BASE_URL;
      this.ws = new WebSocket(wsUrl);

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
  type: 'terminal_input' | 'terminal_output' | 'terminal_clear' | 'terminal_clear_progress' | 'pod_ready' | 'code_execution' | 'file_system' | 'error' | 'connection_established' | 'file_list' | 'file_input_prompt' | 'file_input_response' | 'file_created' | 'file_deleted' | 'file_sync' | 'ping' | 'pong';
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
  toast?: {
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
  };
  files?: { name: string; type: 'file' | 'directory'; path: string; }[];
  sync_info?: {
    updated_files?: string[];
    new_files?: string[];
  };
}

export function useWebSocket() {
  const { state, setConnected, addTerminalLine, setError, setFiles, updateCode, markSaved, clearTerminal, setCurrentFile, setFileContent } = useApp();
  const pathname = usePathname();
  const performFileOperationRef = useRef<((action: string, path: string, content?: string, isManualSave?: boolean) => boolean) | null>(null);
  
  // Import useUserId hook to get current user ID
  const [userId, setUserId] = useState<string | null>(null);
  
  // Get userId from localStorage
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    setUserId(storedUserId);
  }, []);

  // Create stable handler refs to prevent duplicate registrations
  const handlersRegisteredRef = useRef(false);

  // Register handlers only once using refs
  useEffect(() => {
    if (handlersRegisteredRef.current) return;
    
    const handleMessage = (message: WebSocketMessage) => {
      // Handle toast notifications first (before type-specific handling)
      if (message.toast) {
        const { type, message: toastMessage } = message.toast;
        switch (type) {
          case 'success':
            toast.success(toastMessage);
            break;
          case 'error':
            toast.error(toastMessage);
            break;
          case 'info':
            toast.info(toastMessage);
            break;
          case 'warning':
            toast.warning(toastMessage);
            break;
        }
      }

      switch (message.type) {
        case 'connection_established':
          break;

        case 'terminal_output':
          // Always add terminal line, even for empty output, to ensure cursor moves to new line
          addTerminalLine(message.output || '', 'output', message.command);
          break;

        case 'terminal_clear':
          addTerminalLine('CLEAR_TERMINAL', 'output');
          break;

        case 'terminal_clear_progress':
          addTerminalLine('CLEAR_PROGRESS', 'clear_progress');
          break;

        case 'pod_ready':
          addTerminalLine('POD_READY', 'pod_ready');
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
          // Always add terminal line, even for empty output, to ensure cursor moves to new line
          addTerminalLine(message.output || '', 'output', message.command);
          // Update file list from message if available
          if (message.files) {
            setFiles(message.files);
          } else {
            // Fallback: Request fresh file list after file creation
            setTimeout(() => {
              if (performFileOperationRef.current) {
                performFileOperationRef.current('list', '');
              }
            }, 100);
          }
          break;

        case 'file_deleted':
          // Always add terminal line, even for empty output, to ensure cursor moves to new line
          addTerminalLine(message.output || '', 'output', message.command);
          // Update file list from message if available
          if (message.files) {
            setFiles(message.files);
          } else {
            // Fallback: Request fresh file list after file deletion
            setTimeout(() => {
              if (performFileOperationRef.current) {
                performFileOperationRef.current('list', '');
              }
            }, 100);
          }
          break;

        case 'file_system':
          if (message.action === 'read' && message.content && message.path) {
            // Cache the file content and update current code if this is the current file
            setFileContent(message.path, message.content);
            if (state.currentFile === message.path) {
              updateCode(message.content);
            }
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
          } else if (message.action === 'write' && message.content !== undefined && message.path) {
            // Update file content cache and mark as saved
            setFileContent(message.path, message.content);
            // Don't show message in terminal - toast will be shown if backend provides one
          }
          break;

        case 'file_sync':
          if (message.files) {
            // Update file list
            setFiles(message.files);
          }

          // If there are updated or new files, and one of them is currently open, reload it
          if (message.sync_info && state.currentFile) {
            const updatedFiles = message.sync_info.updated_files || [];
            const newFiles = message.sync_info.new_files || [];
            const allChangedFiles = [...updatedFiles, ...newFiles];

            // If the currently open file was modified via terminal, reload its content
            if (allChangedFiles.includes(state.currentFile)) {
              // Request fresh content for the current file
              performFileOperation('read', state.currentFile);
            }
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

  // WebSocket actions using the manager (defined early to avoid dependency issues)
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

  const performFileOperation = useCallback((action: string, path: string, content?: string, isManualSave?: boolean) => {
    const message = {
      type: 'file_system',
      sessionId: state.currentSession?.id || 'default',
      action,
      path,
      ...(content !== undefined && { content }),
      ...(isManualSave !== undefined && { isManualSave })
    };
    console.log('[FileOperation] Sending message:', message);
    return getWebSocketManager().sendMessage(message);
  }, [state.currentSession?.id]);

  // Store in ref so message handlers can access it
  useEffect(() => {
    performFileOperationRef.current = performFileOperation;
  }, [performFileOperation]);

  const saveCurrentFile = useCallback((content: string, filename?: string, isManualSave: boolean = false) => {
    const currentFile = filename || state.currentFile || 'main.py';
    const result = performFileOperation('write', currentFile, content, isManualSave);
    
    // If this is a manual save (not autosave), mark it as saved
    // Don't show terminal message here - backend will send it if needed
    if (isManualSave) {
      markSaved(content);
    }
    
    return result;
  }, [performFileOperation, state.currentFile, markSaved]);
  
  const manualSave = useCallback((content?: string, filename?: string) => {
    const codeToSave = content || state.code;
    console.log('[ManualSave] Saving file:', filename || state.currentFile, 'Manual save: true');
    return saveCurrentFile(codeToSave, filename, true);
  }, [saveCurrentFile, state.code, state.currentFile]);

  const sendFileInputResponse = useCallback((filename: string, content: string) => {
    return getWebSocketManager().sendMessage({
      type: 'file_input_response',
      sessionId: state.currentSession?.id || 'default',
      filename,
      content
    });
  }, [state.currentSession?.id]);

  // Connect when session is available
  useEffect(() => {
    if (state.currentSession && userId) {
      getWebSocketManager().connect(userId);
    }
  }, [state.currentSession?.id, userId]);

  // Workspace entry handling - clear terminal every time a workspace is navigated to
  const workspaceEntryRef = useRef<{ pathname: string | null, timestamp: number }>({ pathname: null, timestamp: 0 });
  useEffect(() => {
    if (
      getWebSocketManager().isConnected() && 
      state.currentSession &&
      pathname &&
      pathname.includes('/workspace/')
    ) {
      const now = Date.now();
      const lastEntry = workspaceEntryRef.current;
      
      const shouldClear = lastEntry.pathname !== pathname || (now - lastEntry.timestamp) > 1000;
      
      if (shouldClear) {
        workspaceEntryRef.current = { pathname, timestamp: now };

        // Immediately clear files to prevent showing stale file list from previous workspace
        setFiles([]);

        const refreshTimeout = setTimeout(() => {
          clearTerminal();
          addTerminalLine('CLEAR_TERMINAL', 'output');
          performFileOperation('list', '');
        }, 50);
        
        return () => clearTimeout(refreshTimeout);
      }
    }
    return undefined;
  }, [pathname, state.currentSession?.id, addTerminalLine, performFileOperation, clearTerminal, setFiles]);
  
  // Auto-load main.py when files are loaded and main.py exists
  useEffect(() => {
    if (
      getWebSocketManager().isConnected() &&
      state.currentSession &&
      state.files.length > 0 &&
      !state.currentFile // Only auto-load if no file is currently selected
    ) {
      const mainFile = state.files.find(file => file.name === 'main.py' && file.type === 'file');
      if (mainFile) {
        setCurrentFile(mainFile.path);
        performFileOperation('read', mainFile.path);
      }
    }
  }, [state.currentSession?.id, state.files.length, state.currentFile, performFileOperation, setCurrentFile]);

  const manager = getWebSocketManager();
  return {
    isConnected: manager.isConnected(),
    connect: () => manager.connect(),
    disconnect: () => manager.disconnect(),
    sendTerminalCommand,
    executeCode,
    performFileOperation,
    saveCurrentFile,
    manualSave,
    sendFileInputResponse,
    sendMessage: manager.sendMessage.bind(manager)
  };
}