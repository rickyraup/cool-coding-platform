'use client';

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

// Validation functions
const validateEmail = (email: string): string | null => {
  if (!email.trim()) return 'Email is required';
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) return 'Please enter a valid email address';
  return null;
};

const validateUsername = (username: string): string | null => {
  if (!username.trim()) return 'Username is required';
  if (username.length < 3) return 'Username must be at least 3 characters';
  if (!/^[a-zA-Z0-9_]+$/.test(username)) return 'Username can only contain letters, numbers, and underscores';
  return null;
};

const validatePassword = (password: string): string | null => {
  if (!password) return 'Password is required';
  if (password.length < 8) return 'Password must be at least 8 characters';
  if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?])/.test(password)) {
    return 'Password must contain at least one uppercase letter, lowercase letter, number, and special character';
  }
  return null;
};

const validateConfirmPassword = (password: string, confirmPassword: string): string | null => {
  if (!confirmPassword) return 'Please confirm your password';
  if (password !== confirmPassword) return 'Passwords do not match';
  return null;
};

export default function HomePage() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [realTimeValidation, setRealTimeValidation] = useState<{[key: string]: 'valid' | 'invalid' | 'neutral'}>({});
  const { login, register, error, isAuthenticated, clearError } = useAuth();
  const router = useRouter();

  // Redirect to dashboard if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);


  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear validation error for this field when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Real-time validation feedback (only for signup, minimal for login)
    let validationStatus: 'valid' | 'invalid' | 'neutral' = 'neutral';
    const newFormData = { ...formData, [name]: value };
    
    if (value.length > 0) {
      if (isLogin) {
        // For login, just check that fields are not empty
        validationStatus = value.trim().length > 0 ? 'valid' : 'invalid';
      } else {
        // For signup, apply full validation rules
        switch (name) {
          case 'email':
            const emailError = validateEmail(value);
            validationStatus = emailError ? 'invalid' : 'valid';
            break;
          case 'username':
            const usernameError = validateUsername(value);
            validationStatus = usernameError ? 'invalid' : 'valid';
            break;
          case 'password':
            const passwordError = validatePassword(value);
            validationStatus = passwordError ? 'invalid' : 'valid';
            break;
          case 'confirmPassword':
            const confirmPasswordError = validateConfirmPassword(newFormData.password, value);
            validationStatus = confirmPasswordError ? 'invalid' : 'valid';
            break;
          default:
            validationStatus = 'neutral';
        }
      }
    }

    setRealTimeValidation(prev => {
      const newValidation = {
        ...prev,
        [name]: validationStatus
      };

      // If password changed during signup, also re-validate confirm password
      if (!isLogin && name === 'password' && newFormData.confirmPassword && newFormData.confirmPassword.length > 0) {
        const confirmPasswordError = validateConfirmPassword(value, newFormData.confirmPassword);
        newValidation['confirmPassword'] = confirmPasswordError ? 'invalid' : 'valid';
      }

      return newValidation;
    });
  };

  // Clear form state when switching between login and signup
  const clearFormState = () => {
    setFormData({ name: '', email: '', username: '', password: '', confirmPassword: '' });
    setValidationErrors({});
    setRealTimeValidation({});
    clearError();
  };

  const switchToLogin = () => {
    setIsLogin(true);
    clearFormState();
  };

  const switchToSignup = () => {
    setIsLogin(false);
    clearFormState();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only validate for signup, not login
    if (!isLogin) {
      // Basic validation for signup
      const errors: {[key: string]: string} = {};
      
      if (!formData.username.trim()) {
        errors['username'] = 'Username is required';
      }
      if (!formData.email.trim()) {
        errors['email'] = 'Email is required';
      }
      if (!formData.password) {
        errors['password'] = 'Password is required';
      }
      
      if (Object.keys(errors).length > 0) {
        setValidationErrors(errors);
        return;
      }
    }

    setIsSubmitting(true);

    try {
      if (isLogin) {
        // Login with username or email
        await login({
          username: formData.email, // The backend now handles both email and username
          password: formData.password
        });
      } else {
        // Register
        await register({
          username: formData.username,
          email: formData.email,
          password: formData.password
        });
      }
      
      // Redirect to dashboard on success
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Authentication error:', err);
      
      // Handle specific registration errors
      if (!isLogin && err?.message) {
        const errorMessage = err.message.toLowerCase();
        if (errorMessage.includes('username') && errorMessage.includes('already')) {
          setValidationErrors({ username: 'This username is already taken' });
        } else if (errorMessage.includes('email') && errorMessage.includes('already')) {
          setValidationErrors({ email: 'This email is already registered' });
        } else if (errorMessage.includes('duplicate')) {
          // Generic duplicate error
          if (errorMessage.includes('username')) {
            setValidationErrors({ username: 'This username is already taken' });
          } else if (errorMessage.includes('email')) {
            setValidationErrors({ email: 'This email is already registered' });
          } else {
            setValidationErrors({ general: 'An account with these details already exists' });
          }
        }
      }
      // Error is also handled by the auth context for display
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8ZGVmcz4KICAgIDxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgogICAgICA8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwgMjU1LCAyNTUsIDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KICAgIDwvcGF0dGVybj4KICA8L2RlZnM+CiAgPHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIgLz4KPC9zdmc+')] opacity-30"></div>
      
      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">⚡</span>
          </div>
          <span className="text-white text-xl font-bold">Coding Workspaces Project</span>
        </div>
        
      </nav>

      {/* Main Content */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Side - Hero Content */}
          <div className="text-white space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                Code in the
                <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent"> Cloud</span>
              </h1>
              <p className="text-xl text-gray-300 leading-relaxed">
                A powerful, browser-based IDE with isolated Python environments 
                and seamless package management.
              </p>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <span className="text-green-400 text-sm">🐍</span>
                </div>
                <span className="text-gray-300">Python 3.11+</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <span className="text-blue-400 text-sm">🐳</span>
                </div>
                <span className="text-gray-300">Docker Isolated</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                  <span className="text-purple-400 text-sm">📦</span>
                </div>
                <span className="text-gray-300">Package Manager</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                  <span className="text-yellow-400 text-sm">⚡</span>
                </div>
                <span className="text-gray-300">Real-time Terminal</span>
              </div>
            </div>

          </div>

          {/* Right Side - Auth Form */}
          <div className="bg-black/20 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
            <div className="space-y-6">
              
              {/* Tab Selector */}
              <div className="flex bg-gray-800 rounded-lg p-1">
                <button
                  onClick={switchToLogin}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    isLogin 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Log In
                </button>
                <button
                  onClick={switchToSignup}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    !isLogin 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Sign Up
                </button>
              </div>

              {/* Form */}
              <form className="space-y-4" onSubmit={handleSubmit}>
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}

                {/* General validation errors */}
                {validationErrors.general && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                    <p className="text-red-400 text-sm">{validationErrors.general}</p>
                  </div>
                )}

                {!isLogin && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Username *
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleInputChange}
                        className={`w-full px-3 py-2 pr-10 bg-gray-800 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-1 ${
                          validationErrors.username 
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                            : realTimeValidation.username === 'valid'
                            ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                            : realTimeValidation.username === 'invalid'
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                            : 'border-gray-700 focus:border-blue-500 focus:ring-blue-500'
                        }`}
                        placeholder="Choose a username"
                        required={!isLogin}
                      />
                      {/* Real-time validation indicator */}
                      {formData.username && realTimeValidation.username !== 'neutral' && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          {realTimeValidation.username === 'valid' ? (
                            <span className="text-green-400 text-sm">✓</span>
                          ) : (
                            <span className="text-red-400 text-sm">✗</span>
                          )}
                        </div>
                      )}
                    </div>
                    {validationErrors.username && (
                      <p className="text-red-400 text-xs mt-1">{validationErrors.username}</p>
                    )}
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    {isLogin ? 'Email or Username *' : 'Email Address *'}
                  </label>
                  <div className="relative">
                    <input
                      type={isLogin ? "text" : "email"}
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className={`w-full px-3 py-2 pr-10 bg-gray-800 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-1 ${
                        isLogin 
                          ? 'border-gray-700 focus:border-blue-500 focus:ring-blue-500'
                          : (!isLogin && validationErrors.email) 
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                            : realTimeValidation.email === 'valid'
                            ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                            : realTimeValidation.email === 'invalid'
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                            : 'border-gray-700 focus:border-blue-500 focus:ring-blue-500'
                      }`}
                      placeholder={isLogin ? "Enter email or username" : "Enter your email address"}
                      required
                    />
                    {/* Real-time validation indicator - show only for signup */}
                    {!isLogin && formData.email && realTimeValidation.email !== 'neutral' && (
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                        {realTimeValidation.email === 'valid' ? (
                          <span className="text-green-400 text-sm">✓</span>
                        ) : (
                          <span className="text-red-400 text-sm">✗</span>
                        )}
                      </div>
                    )}
                  </div>
                  {!isLogin && validationErrors.email && (
                    <p className="text-red-400 text-xs mt-1">{validationErrors.email}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Password *
                  </label>
                  <div className="relative">
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      className={`w-full px-3 py-2 pr-10 bg-gray-800 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-1 ${
                        isLogin 
                          ? 'border-gray-700 focus:border-blue-500 focus:ring-blue-500'
                          : validationErrors.password 
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                            : realTimeValidation.password === 'valid'
                            ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                            : realTimeValidation.password === 'invalid'
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                            : 'border-gray-700 focus:border-blue-500 focus:ring-blue-500'
                      }`}
                      placeholder="Enter your password"
                      required
                    />
                    {/* Real-time validation indicator - show only for signup */}
                    {!isLogin && formData.password && realTimeValidation.password !== 'neutral' && (
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                        {realTimeValidation.password === 'valid' ? (
                          <span className="text-green-400 text-sm">✓</span>
                        ) : (
                          <span className="text-red-400 text-sm">✗</span>
                        )}
                      </div>
                    )}
                  </div>
                  {!isLogin && validationErrors.password && (
                    <p className="text-red-400 text-xs mt-1">{validationErrors.password}</p>
                  )}
                  {!isLogin && !validationErrors.password && (
                    <div className="mt-2">
                      {formData.password && realTimeValidation.password === 'invalid' ? (
                        <div className="space-y-1">
                          <p className="text-gray-500 text-xs">Password requirements:</p>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                            <div className={`flex items-center space-x-1 ${
                              formData.password.length >= 8 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              <span>{formData.password.length >= 8 ? '✓' : '✗'}</span>
                              <span>8+ characters</span>
                            </div>
                            <div className={`flex items-center space-x-1 ${
                              /[A-Z]/.test(formData.password) ? 'text-green-400' : 'text-red-400'
                            }`}>
                              <span>{/[A-Z]/.test(formData.password) ? '✓' : '✗'}</span>
                              <span>Uppercase letter</span>
                            </div>
                            <div className={`flex items-center space-x-1 ${
                              /[a-z]/.test(formData.password) ? 'text-green-400' : 'text-red-400'
                            }`}>
                              <span>{/[a-z]/.test(formData.password) ? '✓' : '✗'}</span>
                              <span>Lowercase letter</span>
                            </div>
                            <div className={`flex items-center space-x-1 ${
                              /\d/.test(formData.password) ? 'text-green-400' : 'text-red-400'
                            }`}>
                              <span>{/\d/.test(formData.password) ? '✓' : '✗'}</span>
                              <span>Number</span>
                            </div>
                            <div className={`flex items-center space-x-1 col-span-2 ${
                              /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(formData.password) ? 'text-green-400' : 'text-red-400'
                            }`}>
                              <span>{/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(formData.password) ? '✓' : '✗'}</span>
                              <span>Special character</span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="text-gray-500 text-xs">
                          Must contain: 8+ chars, uppercase, lowercase, number, special character
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {!isLogin && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Confirm Password *
                    </label>
                    <div className="relative">
                      <input
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        className={`w-full px-3 py-2 pr-10 bg-gray-800 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-1 ${
                          validationErrors.confirmPassword 
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                            : realTimeValidation.confirmPassword === 'valid'
                            ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                            : realTimeValidation.confirmPassword === 'invalid'
                            ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                            : 'border-gray-700 focus:border-blue-500 focus:ring-blue-500'
                        }`}
                        placeholder="Confirm your password"
                        required={!isLogin}
                      />
                      {/* Real-time validation indicator */}
                      {formData.confirmPassword && realTimeValidation.confirmPassword !== 'neutral' && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          {realTimeValidation.confirmPassword === 'valid' ? (
                            <span className="text-green-400 text-sm">✓</span>
                          ) : (
                            <span className="text-red-400 text-sm">✗</span>
                          )}
                        </div>
                      )}
                    </div>
                    {validationErrors.confirmPassword && (
                      <p className="text-red-400 text-xs mt-1">{validationErrors.confirmPassword}</p>
                    )}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (isLogin ? 'Logging In...' : 'Creating Account...') : (isLogin ? 'Log In' : 'Create Account')}
                </button>
              </form>

              {/* Social Login */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-700"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-black/20 text-gray-400">Or continue with</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button 
                  onClick={() => {
                    // TODO: Implement Google OAuth
                    alert('Google OAuth not yet implemented. Please use email/password signup for now.');
                  }}
                  className="flex items-center justify-center py-2 px-4 border border-gray-700 rounded-lg text-gray-300 hover:bg-gray-800 transition-colors"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google
                </button>
                <button 
                  onClick={() => {
                    // TODO: Implement GitHub OAuth
                    alert('GitHub OAuth not yet implemented. Please use email/password signup for now.');
                  }}
                  className="flex items-center justify-center py-2 px-4 border border-gray-700 rounded-lg text-gray-300 hover:bg-gray-800 transition-colors"
                >
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  GitHub
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}