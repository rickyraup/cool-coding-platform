/**
 * API service for communicating with the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

interface CodeSession {
  id: string;
  user_id: string;
  code: string;
  language: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

interface SessionListResponse extends ApiResponse<CodeSession[]> {}
interface SessionResponse extends ApiResponse<CodeSession> {}

interface CreateSessionRequest {
  user_id?: string;
  code?: string;
  language?: string;
}

interface UpdateSessionRequest {
  code?: string;
  language?: string;
  is_active?: boolean;
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

  // Session Management
  async createSession(sessionData?: CreateSessionRequest): Promise<CodeSession> {
    const response = await this.fetchWithErrorHandling<SessionResponse>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData || {}),
    });
    return response.data;
  }

  async getSession(sessionId: string): Promise<CodeSession> {
    const response = await this.fetchWithErrorHandling<SessionResponse>(`/api/sessions/${sessionId}`);
    return response.data;
  }

  async updateSession(sessionId: string, sessionData: UpdateSessionRequest): Promise<CodeSession> {
    const response = await this.fetchWithErrorHandling<SessionResponse>(`/api/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(sessionData),
    });
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.fetchWithErrorHandling(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async getSessions(skip = 0, limit = 100): Promise<CodeSession[]> {
    const response = await this.fetchWithErrorHandling<SessionListResponse>(
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
  CodeSession, 
  CreateSessionRequest, 
  UpdateSessionRequest,
  ApiResponse,
  SessionResponse,
  SessionListResponse
};