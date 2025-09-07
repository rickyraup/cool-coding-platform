// Shared constants across frontend and backend

export const WEBSOCKET_EVENTS = {
  TERMINAL_INPUT: 'terminal_input',
  TERMINAL_OUTPUT: 'terminal_output',
  CODE_EXECUTION: 'code_execution',
  FILE_SYSTEM: 'file_system',
  ERROR: 'error',
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
} as const;

export const API_ENDPOINTS = {
  // Authentication
  AUTH: '/api/auth',
  LOGIN: '/api/auth/login',
  REGISTER: '/api/auth/register',
  LOGOUT: '/api/auth/logout',
  
  // Sessions
  SESSIONS: '/api/sessions',
  SESSION_BY_ID: (id: string) => `/api/sessions/${id}`,
  
  // Code execution
  EXECUTE: '/api/execute',
  
  // File system
  FILES: '/api/files',
  FILE_CONTENT: (path: string) => `/api/files/content?path=${encodeURIComponent(path)}`,
  
  // Code submissions
  SUBMISSIONS: '/api/submissions',
  SUBMISSION_BY_ID: (id: string) => `/api/submissions/${id}`,
  REVIEW_SUBMISSION: (id: string) => `/api/submissions/${id}/review`,
  
  // Users
  USERS: '/api/users',
  USER_PROFILE: '/api/users/profile',
} as const;

export const CONFIG = {
  // Execution limits
  MAX_CODE_SIZE: 1024 * 1024, // 1MB
  MAX_EXECUTION_TIME: 30000, // 30 seconds
  MAX_OUTPUT_SIZE: 1024 * 100, // 100KB
  
  // Session management
  SESSION_TIMEOUT: 1000 * 60 * 60, // 1 hour
  MAX_CONCURRENT_SESSIONS: 10,
  
  // File system
  SANDBOX_ROOT: '/tmp/coding_platform',
  ALLOWED_EXTENSIONS: ['.py', '.txt', '.md', '.json', '.csv'],
  MAX_FILE_SIZE: 1024 * 1024, // 1MB
  
  // Python environment
  PYTHON_VERSION: '3.11',
  REQUIRED_PACKAGES: ['pandas', 'scipy', 'numpy', 'matplotlib'],
  
  // Security
  RATE_LIMIT_REQUESTS: 100,
  RATE_LIMIT_WINDOW: 1000 * 60 * 15, // 15 minutes
} as const;

export const ERROR_CODES = {
  // Authentication
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  
  // Sessions
  SESSION_NOT_FOUND: 'SESSION_NOT_FOUND',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  MAX_SESSIONS_EXCEEDED: 'MAX_SESSIONS_EXCEEDED',
  
  // Code execution
  EXECUTION_TIMEOUT: 'EXECUTION_TIMEOUT',
  EXECUTION_ERROR: 'EXECUTION_ERROR',
  CODE_TOO_LARGE: 'CODE_TOO_LARGE',
  
  // File system
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  INVALID_PATH: 'INVALID_PATH',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  
  // General
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
} as const;

export const USER_ROLES = {
  USER: 'user',
  REVIEWER: 'reviewer',
  ADMIN: 'admin',
} as const;

export const SUBMISSION_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
} as const;