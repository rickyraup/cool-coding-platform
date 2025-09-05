// Core types for the code execution platform

export interface CodeSession {
  id: string;
  userId: string;
  code: string;
  language: 'python';
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
}

export interface TerminalSession {
  id: string;
  sessionId: string;
  pid?: number;
  isActive: boolean;
  createdAt: Date;
}

export interface ExecutionResult {
  success: boolean;
  output: string;
  error?: string;
  executionTime: number;
  exitCode?: number;
}

export interface TerminalCommand {
  id: string;
  sessionId: string;
  command: string;
  output: string;
  timestamp: Date;
  exitCode?: number;
}

export interface FileSystemItem {
  name: string;
  type: 'file' | 'directory';
  path: string;
  size?: number;
  lastModified: Date;
  content?: string; // Only for files when requested
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'reviewer' | 'admin';
  createdAt: Date;
}

export interface CodeSubmission {
  id: string;
  userId: string;
  sessionId: string;
  code: string;
  title: string;
  description?: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewerId?: string;
  reviewComment?: string;
  submittedAt: Date;
  reviewedAt?: Date;
}

// WebSocket message types
export type WebSocketMessage = 
  | TerminalInputMessage
  | TerminalOutputMessage
  | CodeExecutionMessage
  | FileSystemMessage
  | ErrorMessage;

export interface TerminalInputMessage {
  type: 'terminal_input';
  sessionId: string;
  command: string;
}

export interface TerminalOutputMessage {
  type: 'terminal_output';
  sessionId: string;
  output: string;
  timestamp: Date;
}

export interface CodeExecutionMessage {
  type: 'code_execution';
  sessionId: string;
  code: string;
  filename?: string;
}

export interface FileSystemMessage {
  type: 'file_system';
  action: 'read' | 'write' | 'list' | 'delete';
  path: string;
  content?: string;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
  code?: string;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}