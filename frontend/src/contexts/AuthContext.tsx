'use client';

import type { ReactNode } from 'react';
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, AuthResponse, UserLogin, UserCreate } from '@/services/api';
import { apiService } from '@/services/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (loginData: UserLogin) => Promise<AuthResponse>;
  register: (registerData: UserCreate) => Promise<AuthResponse>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user;

  // Load user from localStorage on mount
  useEffect(() => {
    const loadStoredUser = () => {
      try {
        const storedUser = localStorage.getItem('user');
        const storedUserId = localStorage.getItem('userId');
        
        if (storedUser && storedUserId) {
          const userData = JSON.parse(storedUser);
          setUser(userData);
        }
      } catch (err) {
        console.error('Failed to load stored user:', err);
        // Clear invalid stored data
        localStorage.removeItem('user');
        localStorage.removeItem('userId');
      } finally {
        setIsLoading(false);
      }
    };

    loadStoredUser();
  }, []);

  const login = async (loginData: UserLogin): Promise<AuthResponse> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiService.loginUser(loginData);
      
      if (response.success && response.user) {
        setUser(response.user);
        
        // Store user data in localStorage
        localStorage.setItem('user', JSON.stringify(response.user));
        localStorage.setItem('userId', response.data.user_id.toString());
      }
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (registerData: UserCreate): Promise<AuthResponse> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiService.registerUser(registerData);
      
      if (response.success && response.user) {
        setUser(response.user);
        
        // Store user data in localStorage
        localStorage.setItem('user', JSON.stringify(response.user));
        localStorage.setItem('userId', response.data.user_id.toString());
      }
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setError(null);
    
    // Clear stored user data
    localStorage.removeItem('user');
    localStorage.removeItem('userId');
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Helper hook to get current user ID
export function useUserId(): number | null {
  const { user } = useAuth();
  return user?.id ?? null;
}

