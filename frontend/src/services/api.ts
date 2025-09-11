/**
 * API service for communicating with the backend PostgreSQL APIs
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

// User types
interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}

interface UserCreate {
  username: string;
  email: string;
  password: string;
}

interface UserLogin {
  username: string;
  password: string;
}

interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  data: { user_id: number };
}

// Session types (PostgreSQL schema)
interface CodeSession {
  id: number;
  user_id: number;
  name?: string;
  created_at: string;
  updated_at: string;
}

interface SessionCreate {
  user_id: number;
  name?: string;
}

interface SessionUpdate {
  name?: string;
}

// Workspace types
interface WorkspaceItem {
  id: number;
  session_id: number;
  parent_id?: number;
  name: string;
  type: 'file' | 'folder';
  content?: string;
  created_at: string;
  updated_at: string;
  full_path?: string;
}

interface WorkspaceItemCreate {
  session_id: number;
  parent_id?: number;
  name: string;
  type: 'file' | 'folder';
  content?: string;
}

interface WorkspaceItemUpdate {
  name?: string;
  content?: string;
}

interface WorkspaceTreeItem {
  id: number;
  name: string;
  type: 'file' | 'folder';
  full_path: string;
  children?: WorkspaceTreeItem[];
}

// API Response types
interface BaseResponse {
  success: boolean;
  message: string;
}

interface ApiResponse<T> extends BaseResponse {
  data: T;
}

interface SessionListResponse extends BaseResponse {
  data: CodeSession[];
  count: number;
}

interface SessionWithWorkspaceResponse extends BaseResponse {
  session: CodeSession;
  workspace_items: WorkspaceItem[];
  workspace_tree: WorkspaceTreeItem[];
}

interface WorkspaceItemListResponse extends BaseResponse {
  data: WorkspaceItem[];
  count: number;
}

interface WorkspaceTreeResponse extends BaseResponse {
  data: WorkspaceTreeItem[];
}

class ApiService {
  private async fetchWithErrorHandling<T>(
    url: string, 
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.message || errorData?.detail || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error instanceof Error 
        ? error 
        : new Error('An unexpected error occurred');
    }
  }

  // User Authentication
  async registerUser(userData: UserCreate): Promise<AuthResponse> {
    return await this.fetchWithErrorHandling<AuthResponse>('/api/users/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async loginUser(loginData: UserLogin): Promise<AuthResponse> {
    return await this.fetchWithErrorHandling<AuthResponse>('/api/users/login', {
      method: 'POST',
      body: JSON.stringify(loginData),
    });
  }

  async getUser(userId: number): Promise<AuthResponse> {
    return await this.fetchWithErrorHandling<AuthResponse>(`/api/users/${userId}`);
  }

  async getUserByUsername(username: string): Promise<AuthResponse> {
    return await this.fetchWithErrorHandling<AuthResponse>(`/api/users/username/${username}`);
  }

  // PostgreSQL Session Management
  async createSession(sessionData: SessionCreate): Promise<ApiResponse<CodeSession>> {
    return await this.fetchWithErrorHandling<ApiResponse<CodeSession>>('/api/postgres_sessions/', {
      method: 'POST',
      body: JSON.stringify(sessionData),
    });
  }

  async getSession(sessionId: number): Promise<ApiResponse<CodeSession>> {
    return await this.fetchWithErrorHandling<ApiResponse<CodeSession>>(`/api/postgres_sessions/${sessionId}`);
  }

  async updateSession(sessionId: number, sessionData: SessionUpdate): Promise<ApiResponse<CodeSession>> {
    return await this.fetchWithErrorHandling<ApiResponse<CodeSession>>(`/api/postgres_sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(sessionData),
    });
  }

  async deleteSession(sessionId: number): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/postgres_sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async getSessions(userId?: number, skip = 0, limit = 100): Promise<SessionListResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (userId) {
      params.append('user_id', userId.toString());
    }
    return await this.fetchWithErrorHandling<SessionListResponse>(
      `/api/postgres_sessions/?${params}`
    );
  }

  async getSessionWithWorkspace(sessionId: number): Promise<SessionWithWorkspaceResponse> {
    return await this.fetchWithErrorHandling<SessionWithWorkspaceResponse>(
      `/api/postgres_sessions/${sessionId}/workspace`
    );
  }

  // Workspace Item Management
  async createWorkspaceItem(itemData: WorkspaceItemCreate): Promise<ApiResponse<WorkspaceItem>> {
    return await this.fetchWithErrorHandling<ApiResponse<WorkspaceItem>>('/api/workspace/', {
      method: 'POST',
      body: JSON.stringify(itemData),
    });
  }

  async getWorkspaceItem(itemId: number): Promise<ApiResponse<WorkspaceItem>> {
    return await this.fetchWithErrorHandling<ApiResponse<WorkspaceItem>>(`/api/workspace/${itemId}`);
  }

  async updateWorkspaceItem(itemId: number, itemData: WorkspaceItemUpdate): Promise<ApiResponse<WorkspaceItem>> {
    return await this.fetchWithErrorHandling<ApiResponse<WorkspaceItem>>(`/api/workspace/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(itemData),
    });
  }

  async deleteWorkspaceItem(itemId: number): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/workspace/${itemId}`, {
      method: 'DELETE',
    });
  }

  async getSessionWorkspaceItems(sessionId: number, parentId?: number): Promise<WorkspaceItemListResponse> {
    const params = new URLSearchParams();
    if (parentId) {
      params.append('parent_id', parentId.toString());
    }
    const queryString = params.toString();
    return await this.fetchWithErrorHandling<WorkspaceItemListResponse>(
      `/api/workspace/session/${sessionId}${queryString ? `?${queryString}` : ''}`
    );
  }

  async getSessionWorkspaceTree(sessionId: number): Promise<WorkspaceTreeResponse> {
    return await this.fetchWithErrorHandling<WorkspaceTreeResponse>(
      `/api/workspace/session/${sessionId}/tree`
    );
  }

  // Session-Container Workspace Integration
  async loadSessionWorkspace(sessionId: number): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionId}/load`, {
      method: 'POST',
    });
  }

  async saveSessionWorkspace(sessionId: number): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionId}/save`, {
      method: 'POST',
    });
  }

  async getWorkspaceFileContent(sessionId: number, filePath: string): Promise<{ success: boolean; message: string; data: { file_path: string; content: string } }> {
    return await this.fetchWithErrorHandling(`/api/session_workspace/${sessionId}/file/${filePath}`);
  }

  async updateWorkspaceFileContent(sessionId: number, filePath: string, content: string): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionId}/file/${filePath}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async getContainerSessionStatus(sessionId: number): Promise<{ 
    success: boolean; 
    message: string; 
    data: {
      session_id: number;
      container_active: boolean;
      container_id?: string;
      working_dir?: string;
      status: string;
      created_at?: string;
      last_activity?: string;
    }
  }> {
    return await this.fetchWithErrorHandling(`/api/session_workspace/${sessionId}/container/status`);
  }

  async startContainerSession(sessionId: number): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionId}/container/start`, {
      method: 'POST',
    });
  }

  // Legacy Session Management (keep for backwards compatibility)
  async createLegacySession(sessionData?: { user_id?: string; code?: string; language?: string }): Promise<any> {
    return await this.fetchWithErrorHandling('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData || {}),
    });
  }

  async getLegacySession(sessionId: string): Promise<any> {
    return await this.fetchWithErrorHandling(`/api/sessions/${sessionId}`);
  }

  async updateLegacySession(sessionId: string, sessionData: { code?: string; language?: string; is_active?: boolean }): Promise<any> {
    return await this.fetchWithErrorHandling(`/api/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(sessionData),
    });
  }

  async deleteLegacySession(sessionId: string): Promise<void> {
    await this.fetchWithErrorHandling(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async getLegacySessions(skip = 0, limit = 100): Promise<any[]> {
    const response = await this.fetchWithErrorHandling<{ success: boolean; data: any[] }>(
      `/api/sessions?skip=${skip}&limit=${limit}`
    );
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return await this.fetchWithErrorHandling('/api/health/');
  }
}

export const apiService = new ApiService();

// Export types for use in components
export type { 
  // User types
  User,
  UserCreate,
  UserLogin,
  AuthResponse,
  
  // Session types
  CodeSession,
  SessionCreate,
  SessionUpdate,
  SessionListResponse,
  SessionWithWorkspaceResponse,
  
  // Workspace types
  WorkspaceItem,
  WorkspaceItemCreate,
  WorkspaceItemUpdate,
  WorkspaceTreeItem,
  WorkspaceItemListResponse,
  WorkspaceTreeResponse,
  
  // Response types
  BaseResponse,
  ApiResponse
};