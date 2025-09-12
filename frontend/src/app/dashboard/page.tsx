'use client';

import { useAuth } from '../../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiService, CodeSession } from '../../services/api';

export default function DashboardPage() {
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<CodeSession[]>([]);
  const [loadingWorkspaces, setLoadingWorkspaces] = useState(true);
  const [workspacesError, setWorkspacesError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch user's workspaces
  useEffect(() => {
    const fetchWorkspaces = async () => {
      if (!isAuthenticated || !user) return;
      
      try {
        setLoadingWorkspaces(true);
        setWorkspacesError(null);
        
        const response = await apiService.getSessions(user.id);
        setWorkspaces(response.data);
      } catch (error) {
        console.error('Failed to fetch workspaces:', error);
        setWorkspacesError(error instanceof Error ? error.message : 'Failed to load workspaces');
      } finally {
        setLoadingWorkspaces(false);
      }
    };

    fetchWorkspaces();
  }, [isAuthenticated, user]);

  const handleCreateWorkspace = async () => {
    if (!isAuthenticated || !user) return;
    
    try {
      setLoadingWorkspaces(true);
      
      // Create a new session
      const response = await apiService.createSession({
        user_id: user.id,
        name: `New Project ${Date.now()}`
      });
      
      // Navigate to the new workspace
      router.push(`/workspace/${response.data.id}`);
      
    } catch (error) {
      console.error('Failed to create workspace:', error);
      // Could add a toast notification here
    } finally {
      setLoadingWorkspaces(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">⚡</span>
                </div>
                <h1 className="text-white text-xl font-bold">CodeForge</h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-300">
                Welcome, <span className="text-white font-medium">{user.username}</span>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Your Workspaces</h2>
          <p className="text-gray-400">Create and manage your coding projects</p>
        </div>

        {/* Create New Workspace Button */}
        <div className="mb-8">
          <button
            onClick={handleCreateWorkspace}
            disabled={loadingWorkspaces}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="mr-2">+</span>
            Create New Workspace
          </button>
        </div>

        {/* Workspaces Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loadingWorkspaces ? (
            // Loading state
            Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="bg-gray-800 rounded-lg border border-gray-700 p-6 animate-pulse">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gray-700 rounded-lg"></div>
                    <div>
                      <div className="h-5 bg-gray-700 rounded w-32 mb-2"></div>
                      <div className="h-4 bg-gray-700 rounded w-20"></div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="h-4 bg-gray-700 rounded w-24"></div>
                  <div className="h-4 bg-gray-700 rounded w-20"></div>
                </div>
              </div>
            ))
          ) : workspacesError ? (
            // Error state
            <div className="col-span-full">
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-red-800 rounded-full flex items-center justify-center">
                  <span className="text-2xl">⚠️</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Failed to load workspaces</h3>
                <p className="text-gray-400 mb-6">{workspacesError}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium"
                >
                  Try Again
                </button>
              </div>
            </div>
          ) : workspaces.length > 0 ? (
            // Workspaces data
            workspaces.map((workspace) => (
              <div
                key={workspace.id}
                className="bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-all duration-200 hover:shadow-lg cursor-pointer"
              >
                <Link href={`/workspace/${workspace.id}`} className="block p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold">📁</span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{workspace.name || `Workspace ${workspace.id}`}</h3>
                        <p className="text-sm text-gray-400">Python workspace</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm text-gray-400">
                    <span>Created</span>
                    <span>{new Date(workspace.created_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              </div>
            ))
          ) : null}

          {/* Empty State */}
          {!loadingWorkspaces && !workspacesError && workspaces.length === 0 && (
            <div className="col-span-full">
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-800 rounded-full flex items-center justify-center">
                  <span className="text-2xl">📂</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">No workspaces yet</h3>
                <p className="text-gray-400 mb-6">Create your first workspace to get started</p>
                <button
                  onClick={handleCreateWorkspace}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium"
                >
                  <span className="mr-2">+</span>
                  Create New Workspace
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}