interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}

interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  data?: { user_id: number };
  token?: string | null;
}

interface LoginRequest {
  username: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

class AuthService {
  private baseUrl = 'http://localhost:8001/api/users';

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const result = await response.json();
    
    // Store user data in localStorage
    if (result.success && result.user) {
      localStorage.setItem('user', JSON.stringify(result.user));
      localStorage.setItem('isAuthenticated', 'true');
    }

    return result;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    const result = await response.json();
    
    // Store user data in localStorage
    if (result.success && result.user) {
      localStorage.setItem('user', JSON.stringify(result.user));
      localStorage.setItem('isAuthenticated', 'true');
    }

    return result;
  }

  logout(): void {
    localStorage.removeItem('user');
    localStorage.removeItem('isAuthenticated');
  }

  getCurrentUser(): User | null {
    try {
      const userData = localStorage.getItem('user');
      return userData ? JSON.parse(userData) : null;
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    return localStorage.getItem('isAuthenticated') === 'true';
  }

  async getUserById(userId: number): Promise<User> {
    const response = await fetch(`${this.baseUrl}/${userId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }
    
    const result = await response.json();
    return result.user;
  }
}

export const authService = new AuthService();
export type { User, AuthResponse, LoginRequest, RegisterRequest };