'use client';

import { useState, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth, useUserId } from '../contexts/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService, type ReviewRequestCreate } from '../services/api';
import { Auth } from './Auth';
import { ReviewSubmissionModal } from './ReviewSubmissionModal';
import { useRouter, usePathname } from 'next/navigation';

export function Header(): JSX.Element {
  const { state, setSession, setLoading, setError, clearTerminal, setFiles, setCurrentFile, updateCode } = useApp();
  const { user, isAuthenticated, logout } = useAuth();
  const userId = useUserId();
  const { isConnected, executeCode, manualSave } = useWebSocket();
  const [showAuth, setShowAuth] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

   
  const _handleNewSession = useCallback(async (): Promise<void> => {
    if (!isAuthenticated || !userId) {
      setShowAuth(true);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Clear current environment
      clearTerminal();
      setFiles([]);
      setCurrentFile(null);
      
      // Create new PostgreSQL session
      const response = await apiService.createSession({
        user_id: userId,
        name: `Session ${new Date().toLocaleString()}`
      });
      
      // Convert API response to internal format
      const sessionData = {
        id: response.data.id.toString(), // Convert to string for compatibility
        userId: response.data.user_id.toString(),
        code: '', // Empty code - let workspace handle file loading
        language: 'python' as const,
        createdAt: new Date(response.data.created_at),
        updatedAt: new Date(response.data.updated_at),
        isActive: true,
      };

      // Set the new session - don't set code here, let workspace page handle it
      setSession(sessionData);
      
      console.log('New PostgreSQL session created:', sessionData.id);
      
      // Start container session and load workspace
      try {
        await apiService.startContainerSession(response.data.id);
        console.log('Container session started');
      } catch (containerError) {
        console.warn('Failed to start container session:', containerError);
        // Continue anyway - container integration is optional
      }
      
    } catch (error) {
      console.error('Failed to create session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create session');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, userId, setSession, setLoading, setError, clearTerminal, setFiles, setCurrentFile, updateCode]);

  const handleRunCode = useCallback((): void => {
    if (state.code.trim()) {
      executeCode(state.code, 'main.py');
    }
  }, [state.code, executeCode]);

  const handleSave = useCallback((): void => {
    if (!state.currentSession || !state.currentFile) {
      console.warn('No session or file selected');
      return;
    }
    
    // Use WebSocket-based manual save for consistency with autosave
    manualSave();
  }, [state.currentSession, state.currentFile, manualSave]);

  const handleLogout = useCallback(() => {
    logout();
    setShowUserMenu(false);
    // Clear current session
    setSession(null);
    clearTerminal();
    setFiles([]);
    setCurrentFile(null);
    updateCode(''); // Clear code on logout
  }, [logout, setSession, clearTerminal, setFiles, setCurrentFile, updateCode]);

  const handleSubmitReview = useCallback(async (reviewData: { title: string; description?: string; priority: string }): Promise<void> => {
    if (!state.currentSession || !isAuthenticated || !userId) {
      throw new Error('No active session or not authenticated');
    }

    try {
      setLoading(true);
      setError(null);

      const reviewRequest: ReviewRequestCreate = {
        session_id: state.currentSession.id, // Fixed: Use UUID string instead of integer
        title: reviewData.title,
        description: reviewData.description,
        priority: reviewData.priority as 'low' | 'medium' | 'high' | 'urgent',
      };

      const response = await apiService.createReviewRequest(reviewRequest);
      console.log('Review request created:', response.data);
      
      // Show success message or redirect
      alert('Review request submitted successfully!');
      
    } catch (error) {
      console.error('Failed to submit review request:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [state.currentSession, isAuthenticated, userId, setLoading, setError]);

  return (
    <>
      <header className="bg-gradient-to-r from-gray-800 to-gray-750 border-b border-gray-600 px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-white tracking-tight">
                Code Execution Platform
              </h1>
              
              {/* Navigation Buttons */}
              {isAuthenticated && (
                <div className="flex items-center space-x-2">
                  {(pathname?.startsWith('/workspace/') || pathname?.startsWith('/reviews')) && (
                    <button
                      onClick={() => router.push('/dashboard')}
                      className="px-3 py-1.5 text-sm font-medium bg-gray-700 hover:bg-gray-600 text-gray-200 hover:text-white rounded-md transition-colors"
                    >
                      ← Dashboard
                    </button>
                  )}
                  {!pathname?.startsWith('/reviewers') && (
                    <button
                      onClick={() => router.push('/reviewers')}
                      className="px-3 py-1.5 text-sm font-medium bg-purple-700 hover:bg-purple-600 text-purple-200 hover:text-white rounded-md transition-colors"
                    >
                      👥 Reviewers
                    </button>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-3 bg-gray-700/50 px-3 py-1.5 rounded-lg">
              <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-red-400 shadow-sm shadow-red-400/50'}`} />
              <span className={`text-sm font-medium ${isConnected ? 'text-emerald-300' : 'text-red-300'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            {state.currentSession && (
              <div className="bg-blue-500/20 px-3 py-1.5 rounded-lg border border-blue-400/30">
                <span className="text-sm font-mono text-blue-300">
                  Session: {state.currentSession.id.substring(0, 8)}...
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            {/* Authentication Status */}
            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center space-x-2 bg-gray-700/50 hover:bg-gray-600/50 px-3 py-2 rounded-lg transition-colors"
                >
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-white text-sm font-medium">{user.username}</span>
                  <span className="text-gray-400">▼</span>
                </button>
                
                {showUserMenu && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-50">
                    <div className="p-3 border-b border-gray-600">
                      <div className="text-white text-sm font-medium">{user.username}</div>
                      <div className="text-gray-400 text-xs">{user.email}</div>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-2 text-red-300 hover:bg-gray-700 transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="px-4 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-500 active:bg-purple-700 text-white rounded-lg transition-all duration-200 shadow-sm"
              >
                Sign In
              </button>
            )}

            {/* Action Buttons */}
            
            <button 
              onClick={handleRunCode}
              className="px-4 py-2 text-sm font-medium bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              disabled={!isConnected || state.isLoading || !state.code.trim()}
            >
              ▶ Run Code
            </button>

            <button 
              onClick={handleSave}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm ${
                state.isAutosaveEnabled || !state.hasUnsavedChanges || !state.currentFile
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                  : 'bg-gray-600 hover:bg-gray-500 active:bg-gray-700 text-white'
              }`}
              disabled={state.isAutosaveEnabled || !state.hasUnsavedChanges || !state.currentFile || state.isLoading}
              title={state.isAutosaveEnabled ? 'Autosave is enabled' : 'Save file (Ctrl+S)'}
            >
              💾 Save
            </button>

            {/* Review Submission Button - only show in workspace */}
            {pathname?.startsWith('/workspace/') && state.currentSession && isAuthenticated && (
              <button 
                onClick={() => setShowReviewModal(true)}
                className="px-4 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-500 active:bg-purple-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                disabled={state.isLoading}
              >
                📝 Submit for Review
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Authentication Modal */}
      {showAuth && (
        <Auth onClose={() => setShowAuth(false)} />
      )}

      {/* Review Submission Modal */}
      {showReviewModal && state.currentSession && (
        <ReviewSubmissionModal
          sessionId={state.currentSession.id}
          isOpen={showReviewModal}
          onClose={() => setShowReviewModal(false)}
          onSubmit={handleSubmitReview}
        />
      )}

      {/* Click outside to close user menu */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </>
  );
}