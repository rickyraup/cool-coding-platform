'use client';

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { CodeSession } from '../../services/api';
import { apiService } from '../../services/api';

export default function DashboardPage(): React.JSX.Element {
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<CodeSession[]>([]);
  const [loadingWorkspaces, setLoadingWorkspaces] = useState(true);
  const [workspacesError, setWorkspacesError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalWorkspaces, setTotalWorkspaces] = useState(0);
  const [workspacesPerPage] = useState(16); // 4 columns * 4 rows on xl screens

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch user's workspaces with pagination
  useEffect(() => {
    const fetchWorkspaces = async (): Promise<void> => {
      if (!isAuthenticated || !user) return;

      try {
        setLoadingWorkspaces(true);
        setWorkspacesError(null);

        const skip = (currentPage - 1) * workspacesPerPage;
        const workspacesResponse = await apiService.getSessions(user.id, skip, workspacesPerPage);

        setWorkspaces(workspacesResponse.data);
        setTotalWorkspaces(workspacesResponse.count);
      } catch (error) {
        console.error('Failed to fetch workspaces:', error);
        setWorkspacesError(error instanceof Error ? error.message : 'Failed to load workspaces');
      } finally {
        setLoadingWorkspaces(false);
      }
    };

    fetchWorkspaces();
  }, [isAuthenticated, user, currentPage, workspacesPerPage]);

  // Helper function to generate a human-readable ID from UUID
  const getHumanReadableId = (uuid: string) => {
    // Take the first 8 characters of the UUID for a shorter, human-readable format
    return uuid.substring(0, 8).toUpperCase();
  };

  const handleShowCreateModal = () => {
    setNewProjectName('');
    setShowCreateModal(true);
  };

  const handleCreateWorkspace = async () => {
    if (!isAuthenticated || !user || !newProjectName.trim()) return;
    
    try {
      setIsCreating(true);
      
      // Create a new session
      const response = await apiService.createSession({
        user_id: user.id,
        name: newProjectName.trim()
      });
      
      // Close modal and reset state
      setShowCreateModal(false);
      setNewProjectName('');
      
      // Navigate to the new workspace
      router.push(`/workspace/${response.data.id}`);
      
    } catch (error) {
      console.error('Failed to create workspace:', error);
      // Could add a toast notification here
    } finally {
      setIsCreating(false);
    }
  };

  const handleCancelCreate = () => {
    setShowCreateModal(false);
    setNewProjectName('');
  };

  const totalPages = Math.ceil(totalWorkspaces / workspacesPerPage);
  
  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };
  
  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };
  
  const handlePageClick = (page: number) => {
    setCurrentPage(page);
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
                <h1 className="text-white text-xl font-bold">Coding Workspaces Project</h1>
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
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Your Workspaces</h2>
              <p className="text-gray-400">
                Create and manage your coding projects
                {totalWorkspaces > 0 && (
                  <span className="ml-2">
                    ({totalWorkspaces} workspace{totalWorkspaces !== 1 ? 's' : ''})
                  </span>
                )}
              </p>
            </div>
            {totalWorkspaces > workspacesPerPage && (
              <div className="text-sm text-gray-400">
                Page {currentPage} of {totalPages}
              </div>
            )}
          </div>
        </div>

        {/* Code Reviews Section - Disabled */}
        <div className="mb-8 bg-gradient-to-r from-gray-800/40 to-gray-700/40 border border-gray-600/30 rounded-lg p-6 opacity-60">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="text-xl font-semibold text-gray-300">Code Reviews</h3>
                <span className="px-2 py-1 bg-yellow-600/20 text-yellow-400 text-xs font-medium rounded-md border border-yellow-500/30">
                  🚧 Work in Progress
                </span>
              </div>
              <p className="text-gray-500 text-sm">Review system is currently being updated</p>
            </div>
            <button
              disabled
              className="px-4 py-2 bg-gray-600 text-gray-400 rounded-lg text-sm font-medium cursor-not-allowed"
            >
              View All Reviews →
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-gray-800/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-gray-500">—</div>
              <div className="text-sm text-gray-500">Pending Reviews</div>
            </div>
            <div className="bg-gray-800/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-gray-500">—</div>
              <div className="text-sm text-gray-500">In Review</div>
            </div>
            <div className="bg-gray-800/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-gray-500">—</div>
              <div className="text-sm text-gray-500">Approved</div>
            </div>
            <div className="bg-gray-800/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-gray-500">—</div>
              <div className="text-sm text-gray-500">Total Requests</div>
            </div>
          </div>

        </div>

        {/* Create New Workspace Button */}
        <div className="mb-8">
          <button
            onClick={handleShowCreateModal}
            disabled={loadingWorkspaces}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="mr-2">+</span>
            Create New Workspace
          </button>
        </div>

        {/* Workspaces Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
            workspaces.map((workspace) => {
              return (
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
                          <h3 className="text-lg font-semibold text-white">{workspace.name ?? `Workspace ${getHumanReadableId(workspace.id)}`}</h3>
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
              );
            })
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
                  onClick={handleShowCreateModal}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium"
                >
                  <span className="mr-2">+</span>
                  Create New Workspace
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Pagination Controls */}
        {totalWorkspaces > workspacesPerPage && (
          <div className="mt-8 flex items-center justify-center space-x-2">
            {/* Previous Button */}
            <button
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              Previous
            </button>

            {/* Page Numbers */}
            <div className="flex space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, index) => {
                // Calculate which page numbers to show (max 5)
                const startPage = Math.max(1, currentPage - 2);
                const endPage = Math.min(totalPages, startPage + 4);
                const adjustedStartPage = Math.max(1, endPage - 4);
                const pageNumber = adjustedStartPage + index;
                
                if (pageNumber > totalPages) return null;
                
                return (
                  <button
                    key={pageNumber}
                    onClick={() => handlePageClick(pageNumber)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      currentPage === pageNumber
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                        : 'bg-gray-800 border border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    {pageNumber}
                  </button>
                );
              })}
            </div>

            {/* Next Button */}
            <button
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              Next
            </button>
          </div>
        )}
      </main>

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black bg-opacity-75"
            onClick={handleCancelCreate}
          ></div>
          
          {/* Modal */}
          <div className="relative bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 border border-gray-700">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Create New Workspace</h3>
                <button
                  onClick={handleCancelCreate}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="mb-6">
                <label htmlFor="project-name" className="block text-sm font-medium text-gray-300 mb-2">
                  Project Name
                </label>
                <input
                  id="project-name"
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && newProjectName.trim()) {
                      handleCreateWorkspace();
                    }
                  }}
                  placeholder="My Awesome Project"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                  disabled={isCreating}
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={handleCancelCreate}
                  disabled={isCreating}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateWorkspace}
                  disabled={!newProjectName.trim() || isCreating}
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCreating ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}