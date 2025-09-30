'use client';

import { useState, useCallback } from 'react';
import { useApp } from '../contexts/AppContext';
import { useAuth, useUserId } from '../contexts/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/api';
import { Auth } from './Auth';
import WorkspaceShutdownLoader from './WorkspaceShutdownLoader';
import { useRouter, usePathname } from 'next/navigation';

interface HeaderProps {
  reviewStatus?: {
    isUnderReview: boolean;
    isReviewer?: boolean;
    reviewRequest?: any;
  };
  onReviewStatusChange?: () => void;
}

export function Header({ reviewStatus, onReviewStatusChange }: HeaderProps = {}): JSX.Element {
  const { state, setSession, setLoading, setError, setCurrentFile, resetAllState } = useApp();
  const { user, isAuthenticated, logout } = useAuth();
  const userId = useUserId();
  const { isConnected, manualSave } = useWebSocket();
  const [showAuth, setShowAuth] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isShuttingDown, setIsShuttingDown] = useState(false);
  const router = useRouter();
  const pathname = usePathname();


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
    // Reset all app state on logout
    resetAllState();
  }, [logout, resetAllState]);

  const handleWorkspaceShutdown = useCallback(async (): Promise<void> => {
    if (!pathname?.startsWith('/workspace/')) return;

    const workspaceId = pathname.split('/workspace/')[1];
    if (!workspaceId) return;

    try {
      setIsShuttingDown(true);

      // Call the shutdown endpoint
      const result = await apiService.shutdownWorkspace(workspaceId);

      if (result.success) {
        console.log('Workspace shutdown successful:', result);

        // Reset all app state completely to ensure clean workspace switching
        resetAllState();

        // Navigate to dashboard only after successful shutdown
        router.push('/dashboard');
      } else {
        console.error('Workspace shutdown failed:', result);
        // Still navigate but show error
        resetAllState();
        setError(`Shutdown warning: ${result.message}`);
        router.push('/dashboard');
      }
    } catch (error) {
      console.error('Error during workspace shutdown:', error);
      // Still navigate to prevent being stuck
      resetAllState();
      setError(`Shutdown error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      router.push('/dashboard');
    } finally {
      setIsShuttingDown(false);
    }
  }, [pathname, router, resetAllState, setError]);


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
                  {(pathname?.startsWith('/workspace/') || pathname?.startsWith('/reviews') || pathname?.startsWith('/review/')) && (
                    <button
                      onClick={pathname?.startsWith('/workspace/') ? handleWorkspaceShutdown : () => router.push(pathname?.startsWith('/review/') ? '/reviews' : '/dashboard')}
                      disabled={isShuttingDown}
                      className="px-3 py-1.5 text-sm font-medium bg-gray-700 hover:bg-gray-600 text-gray-200 hover:text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isShuttingDown ? 'Shutting down...' : pathname?.startsWith('/review/') ? '← Reviews' : '← Dashboard'}
                    </button>
                  )}
                </div>
              )}
            </div>
            
            {!pathname?.startsWith('/reviews') && !pathname?.startsWith('/review/') && (
              <div className="flex items-center space-x-3 bg-gray-700/50 px-3 py-1.5 rounded-lg">
                <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-red-400 shadow-sm shadow-red-400/50'}`} />
                <span className={`text-sm font-medium ${isConnected ? 'text-emerald-300' : 'text-red-300'}`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            )}
            
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
            

            {/* Save Button - only show in workspace for non-reviewers */}
            {pathname?.startsWith('/workspace/') && (reviewStatus === undefined || !reviewStatus?.isReviewer) && (
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
            )}

          </div>
        </div>
      </header>

      {/* Authentication Modal */}
      {showAuth && (
        <Auth onClose={() => setShowAuth(false)} />
      )}


      {/* Click outside to close user menu */}
      {showUserMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowUserMenu(false)}
        />
      )}

      {/* Workspace Shutdown Loader */}
      <WorkspaceShutdownLoader isVisible={isShuttingDown} />
    </>
  );
}