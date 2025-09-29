/**
 * API service for communicating with the backend PostgreSQL APIs
 */

const API_BASE_URL = process.env['NEXT_PUBLIC_API_URL'] ?? 'http://localhost:8002';

// User types
interface User {
  id: number;
  username: string;
  email: string;
  is_reviewer?: boolean;
  reviewer_level?: number;
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

// Legacy Session type for backwards compatibility
interface LegacySession {
  id: string;
  user_id?: string;
  code?: string;
  language?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

// Session types (PostgreSQL schema)
interface CodeSession {
  id: string;  // UUID string - changed from number to string for security
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

// Review types
interface ReviewRequest {
  id: number;
  session_id: number;
  submitted_by: number;
  assigned_to?: number;
  title: string;
  description?: string;
  status: 'pending' | 'in_review' | 'approved' | 'rejected' | 'requires_changes';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  submitted_at?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
}

interface ReviewRequestCreate {
  session_id: string; // Fixed: UUID string instead of number
  title: string;
  description?: string | undefined;
  priority?: 'low' | 'medium' | 'high' | 'urgent' | undefined;
  assigned_to?: number | undefined;
}

interface ReviewRequestUpdate {
  title?: string;
  description?: string;
  status?: 'pending' | 'in_review' | 'approved' | 'rejected' | 'requires_changes';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to?: number;
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
  workspace_items: any[];
  workspace_tree: any[];
}

interface ReviewRequestListResponse extends BaseResponse {
  data: ReviewRequest[];
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

  async getSession(sessionUuid: string, userId?: number): Promise<ApiResponse<CodeSession>> {
    const params = new URLSearchParams();
    if (userId) {
      params.append('user_id', userId.toString());
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return await this.fetchWithErrorHandling<ApiResponse<CodeSession>>(`/api/postgres_sessions/${sessionUuid}${queryString}`);
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

  async getSessionWithWorkspace(sessionUuid: string, userId?: number): Promise<SessionWithWorkspaceResponse> {
    const params = new URLSearchParams();
    if (userId) {
      params.append('user_id', userId.toString());
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return await this.fetchWithErrorHandling<SessionWithWorkspaceResponse>(
      `/api/postgres_sessions/${sessionUuid}/workspace${queryString}`
    );
  }

  // Session-Container Workspace Integration
  async loadSessionWorkspace(sessionUuid: string): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionUuid}/load`, {
      method: 'POST',
    });
  }

  async saveSessionWorkspace(sessionUuid: string): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionUuid}/save`, {
      method: 'POST',
    });
  }

  async getWorkspaceFileContent(sessionUuid: string, filePath: string): Promise<{ success: boolean; message: string; data: { file_path: string; content: string } }> {
    return await this.fetchWithErrorHandling(`/api/session_workspace/${sessionUuid}/file/${filePath}`);
  }

  async updateWorkspaceFileContent(sessionUuid: string, filePath: string, content: string): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionUuid}/file/${filePath}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async getContainerSessionStatus(sessionUuid: string): Promise<{ 
    success: boolean; 
    message: string; 
    data: {
      session_id: number;
      session_uuid: string;
      container_active: boolean;
      container_id?: string;
      working_dir?: string;
      status: string;
      created_at?: string;
      last_activity?: string;
    }
  }> {
    return await this.fetchWithErrorHandling(`/api/session_workspace/${sessionUuid}/container/status`);
  }

  async startContainerSession(sessionUuid: string): Promise<BaseResponse> {
    return await this.fetchWithErrorHandling<BaseResponse>(`/api/session_workspace/${sessionUuid}/container/start`, {
      method: 'POST',
    });
  }

  // Legacy Session Management (keep for backwards compatibility)
  async createLegacySession(sessionData?: { user_id?: string; code?: string; language?: string }): Promise<LegacySession> {
    return await this.fetchWithErrorHandling('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData ?? {}),
    });
  }

  async getLegacySession(sessionId: string): Promise<LegacySession> {
    return await this.fetchWithErrorHandling(`/api/sessions/${sessionId}`);
  }

  async updateLegacySession(sessionId: string, sessionData: { code?: string; language?: string; is_active?: boolean }): Promise<LegacySession> {
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

  async getLegacySessions(skip = 0, limit = 100): Promise<LegacySession[]> {
    const response = await this.fetchWithErrorHandling<{ success: boolean; data: LegacySession[] }>(
      `/api/sessions?skip=${skip}&limit=${limit}`
    );
    return response.data;
  }

  // Review Management
  async createReviewRequest(reviewData: ReviewRequestCreate): Promise<ApiResponse<ReviewRequest>> {
    return await this.fetchWithErrorHandling<ApiResponse<ReviewRequest>>('/api/reviews/', {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  async getReviewRequest(reviewId: number): Promise<ApiResponse<ReviewRequest>> {
    return await this.fetchWithErrorHandling<ApiResponse<ReviewRequest>>(`/api/reviews/${reviewId}`);
  }

  async updateReviewRequest(reviewId: number, updateData: ReviewRequestUpdate): Promise<ApiResponse<ReviewRequest>> {
    return await this.fetchWithErrorHandling<ApiResponse<ReviewRequest>>(`/api/reviews/${reviewId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async getMyReviewRequests(status?: string): Promise<ReviewRequestListResponse> {
    const params = new URLSearchParams();
    params.append('my_requests', 'true');
    if (status) {
      params.append('status', status);
    }
    const data = await this.fetchWithErrorHandling<ReviewRequest[]>(`/api/reviews/?${params}`);
    return { success: true, message: 'Success', data, count: data.length };
  }

  async getAssignedReviews(status?: string): Promise<ReviewRequestListResponse> {
    const params = new URLSearchParams();
    params.append('assigned_to_me', 'true');
    if (status) {
      params.append('status', status);
    }
    const data = await this.fetchWithErrorHandling<ReviewRequest[]>(`/api/reviews/?${params}`);
    return { success: true, message: 'Success', data, count: data.length };
  }

  async getReviewOverview(): Promise<{ total_pending: number; total_in_review: number; total_approved: number; total_rejected: number; my_pending_reviews: number; my_assigned_reviews: number }> {
    return await this.fetchWithErrorHandling('/api/reviews/stats/overview');
  }

  async getReviewStatusForSession(sessionId: string): Promise<{
    reviewRequest: ReviewRequest | null;
    isReviewer: boolean;
    canSubmitForReview: boolean;
  }> {
    return await this.fetchWithErrorHandling(`/api/reviews/session/${sessionId}/status`);
  }

  async updateReviewStatus(reviewId: number, status: 'pending' | 'in_review' | 'approved' | 'rejected' | 'requires_changes'): Promise<ApiResponse<ReviewRequest>> {
    return await this.fetchWithErrorHandling<ApiResponse<ReviewRequest>>(`/api/reviews/${reviewId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return await this.fetchWithErrorHandling('/api/health/');
  }

  // Reviewer Management
  async getReviewers(): Promise<{ success: boolean; data: User[]; total: number }> {
    return await this.fetchWithErrorHandling<{ success: boolean; data: User[]; total: number }>('/api/users/reviewers');
  }

  async getCurrentUser(): Promise<User> {
    return await this.fetchWithErrorHandling<User>('/api/users/me');
  }

  async toggleReviewerStatus(isReviewer: boolean, reviewerLevel: number = 1): Promise<{ success: boolean; message: string; user: User }> {
    return await this.fetchWithErrorHandling<{ success: boolean; message: string; user: User }>('/api/users/me/reviewer-status', {
      method: 'PUT',
      body: JSON.stringify({
        is_reviewer: isReviewer,
        reviewer_level: reviewerLevel
      }),
    });
  }

  // Workspace Shutdown
  async shutdownWorkspace(workspaceId: string): Promise<{ success: boolean; message: string; workspace_id: string; session_id?: string; container_cleaned?: boolean }> {
    const FASTAPI_BASE_URL = process.env['NEXT_PUBLIC_API_URL'] ?? 'http://localhost:8002';
    const baseUrl = FASTAPI_BASE_URL.endsWith('/') ? FASTAPI_BASE_URL.slice(0, -1) : FASTAPI_BASE_URL;
    const response = await fetch(`${baseUrl}/workspace/${workspaceId}/shutdown`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
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

  // Review types
  ReviewRequest,
  ReviewRequestCreate,
  ReviewRequestUpdate,
  ReviewRequestListResponse,

  // Response types
  BaseResponse,
  ApiResponse
};