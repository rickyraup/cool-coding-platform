/**
 * API service for communicating with the backend
 */

const API_BASE_URL = process.env['NEXT_PUBLIC_API_URL'] ?? 'http://localhost:8002';

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

// Session types
interface CodeSession {
  id: string;  // UUID string
  user_id: number;
  name?: string;
  created_at: string;
  updated_at: string;
}

interface SessionCreate {
  user_id: number;
  name?: string;
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

class ApiService {
  private async fetchWithErrorHandling<T>(
    url: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      // Normalize URL to avoid double slashes
      const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
      const normalizedUrl = url.startsWith('/') ? url : `/${url}`;
      const response = await fetch(`${baseUrl}${normalizedUrl}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.message ?? errorData?.detail ?? `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
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

  // Session Management
  async createSession(sessionData: SessionCreate): Promise<ApiResponse<CodeSession>> {
    return await this.fetchWithErrorHandling<ApiResponse<CodeSession>>('/api/sessions/', {
      method: 'POST',
      body: JSON.stringify(sessionData),
    });
  }

  async getSession(sessionUuid: string, userId?: number): Promise<ApiResponse<CodeSession>> {
    const params = new URLSearchParams();
    if (userId) {
      params.append('user_id', userId.toString());
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return await this.fetchWithErrorHandling<ApiResponse<CodeSession>>(`/api/sessions/${sessionUuid}${queryString}`);
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
      `/api/sessions/?${params}`
    );
  }

  // Workspace Shutdown
  async shutdownWorkspace(workspaceId: string): Promise<{ success: boolean; message: string; workspace_id: string; session_id?: string; container_cleaned?: boolean }> {
    return await this.fetchWithErrorHandling(`/workspace/${workspaceId}/shutdown`, {
      method: 'POST',
    });
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
  SessionListResponse
};