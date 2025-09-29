'use client';

import { CodeEditor } from '../../../components/CodeEditor';
import { Terminal } from '../../../components/Terminal';
import { Header } from '../../../components/Header';
import { FileExplorer } from '../../../components/FileExplorer';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { useEffect, useState, use } from 'react';
import { useApp } from '../../../context/AppContext';
import { apiService, type ReviewRequest } from '../../../services/api';
import { getWorkspaceFiles, getFileContent, getWorkspaceStatus, ensureDefaultFiles } from '../../../services/workspaceApi';
import WorkspaceStartupLoader from '../../../components/WorkspaceStartupLoader';
import { useAuth, useUserId } from '../../../contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

export default function WorkspacePage({ params: paramsPromise }: WorkspacePageProps) {
  const params = use(paramsPromise);
  const { state, setSession, setLoading, updateCode, setCurrentFile, setFiles, clearTerminal } = useApp();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const userId = useUserId();
  const router = useRouter();
  const [sessionLoadError, setSessionLoadError] = useState<string | null>(null);
  const [fastLoading, setFastLoading] = useState(false); // Show content as soon as session loads
  const [workspaceInitialized, setWorkspaceInitialized] = useState(false);
  const [showStartupLoader, setShowStartupLoader] = useState(true);
  const [reviewStatus, setReviewStatus] = useState<{ isUnderReview: boolean; reviewRequest?: ReviewRequest; isReviewer?: boolean }>({ isUnderReview: false });
  const [isProcessingReview, setIsProcessingReview] = useState(false);

  // Redirect to home if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, authLoading, router]);

  // Check workspace initialization status
  useEffect(() => {
    const checkWorkspaceStatus = async () => {
      if (!isAuthenticated || authLoading || !userId) return;

      const sessionUuid = params.id;
      if (!sessionUuid || sessionUuid.trim() === '') return;

      try {
        // Check workspace status periodically until it's ready
        const checkStatus = async (): Promise<boolean> => {
          const status = await getWorkspaceStatus(sessionUuid);

          if (status.status === 'ready' && status.initialized) {
            setWorkspaceInitialized(true);
            setShowStartupLoader(false);
            return true;
          } else if (status.status === 'empty') {
            // Initialize workspace with default files
            await ensureDefaultFiles(sessionUuid);
            // Check again after initialization
            return false;
          } else if (status.status === 'error' || status.status === 'not_found') {
            setSessionLoadError(status.message);
            setShowStartupLoader(false);
            return true;
          }

          return false;
        };

        const isReady = await checkStatus();

        if (!isReady) {
          // Poll every 1 second until workspace is ready
          const pollInterval = setInterval(async () => {
            const ready = await checkStatus();
            if (ready) {
              clearInterval(pollInterval);
            }
          }, 1000);

          // Cleanup interval on unmount
          return () => clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Failed to check workspace status:', error);
        setSessionLoadError('Failed to initialize workspace');
        setShowStartupLoader(false);
      }
    };

    checkWorkspaceStatus();
  }, [params.id, isAuthenticated, authLoading, userId]);

  // Load session data
  useEffect(() => {
    const loadSession = async () => {
      if (!isAuthenticated || authLoading || !userId || !workspaceInitialized) return;
      
      try {
        setLoading(true);
        setSessionLoadError(null);
        
        // Clear terminal state when loading a new workspace
        // This ensures each workspace starts with a fresh terminal
        clearTerminal();
        
        // Use session UUID directly (no parsing needed)
        const sessionUuid = params.id;
        if (!sessionUuid || sessionUuid.trim() === '') {
          throw new Error(`Invalid session UUID: ${params.id}`);
        }
        
        // Load session metadata from API
        const sessionResponse = await apiService.getSession(sessionUuid, userId);

        // Convert API session to AppContext session format
        const session = {
          id: sessionResponse.data.id.toString(),
          userId: sessionResponse.data.user_id.toString(),
          code: '', // Will be loaded from workspace API
          language: 'python' as const,
          createdAt: new Date(sessionResponse.data.created_at),
          updatedAt: new Date(sessionResponse.data.updated_at),
          isActive: true
        };

        // Set session in context
        setSession(session);

        // Load workspace files using new clean API
        try {
          console.log('Loading workspace files for UUID:', sessionUuid);

          // Get all files in workspace
          let files = await getWorkspaceFiles(sessionUuid);
          console.log('Files loaded:', files);

          // Note: Default file creation is handled by the backend automatically
          console.log(`Loaded ${files.length} files from workspace`);
          if (files.length === 0) {
            console.log('No files found in workspace - backend will handle default creation if needed');
          }

          // Set files in context
          setFiles(files);

          // Auto-select main.py if it exists
          const mainFile = files.find(file => file.name === 'main.py');
          if (mainFile) {
            console.log('Auto-selecting main.py');
            setCurrentFile(mainFile.path);

            // Load main.py content
            const fileContent = await getFileContent(sessionUuid, mainFile.name);
            updateCode(fileContent.content);
            console.log('Main.py content loaded:', fileContent.content.length, 'characters');
          }

        } catch (fileError) {
          console.error('Failed to load workspace files:', fileError);
          setSessionLoadError('Failed to load workspace files');
        }

        setFastLoading(true); // Enable fast loading to show UI immediately

        console.log('Workspace loaded successfully using new API');
        
      } catch (error) {
        console.error('Failed to load session:', error);
        setSessionLoadError(error instanceof Error ? error.message : 'Failed to load workspace');
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [params.id, isAuthenticated, authLoading, userId, workspaceInitialized, clearTerminal]); // clearTerminal is stable from useCallback

  // Load review status for this session
  useEffect(() => {
    const loadReviewStatus = async () => {
      if (!isAuthenticated || authLoading || !params.id) return;

      try {
        const status = await apiService.getReviewStatusForSession(params.id);
        setReviewStatus(status);
        console.log('Review status loaded:', status);
      } catch (error) {
        console.error('Failed to load review status:', error);
      }
    };

    loadReviewStatus();
  }, [params.id, isAuthenticated, authLoading]);

  // Handler for reviewer actions
  const handleReviewAction = async (action: 'approved' | 'rejected' | 'requires_changes') => {
    if (!reviewStatus.reviewRequest || !reviewStatus.isReviewer) return;

    try {
      setIsProcessingReview(true);
      await apiService.updateReviewStatus(reviewStatus.reviewRequest.id, action);

      // Refresh review status
      const updatedStatus = await apiService.getReviewStatusForSession(params.id);
      setReviewStatus(updatedStatus);

      // Show success message
      const actionText = action.replace('_', ' ').toLowerCase();
      alert(`Review ${actionText} successfully!`);

    } catch (error) {
      console.error('Failed to update review status:', error);
      alert('Failed to update review status. Please try again.');
    } finally {
      setIsProcessingReview(false);
    }
  };

  // Show startup loader while workspace is initializing
  if (showStartupLoader) {
    return <WorkspaceStartupLoader isVisible={true} message="Starting up workspace..." />;
  }

  // Loading state - only show spinner if we don't have basic session data
  if (authLoading || (state.isLoading && !fastLoading && !state.currentSession)) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <div className="mb-4 text-xl">Loading workspace...</div>
          <div className="text-gray-400">Please wait</div>
        </div>
      </div>
    );
  }

  // Error state
  if (sessionLoadError) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <div className="mb-4 text-xl text-red-400">Failed to load workspace</div>
          <div className="mb-6 text-gray-400">{sessionLoadError}</div>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900 text-white overflow-hidden">
      <Header />

      {/* Review Status Banner */}
      {reviewStatus.isUnderReview && reviewStatus.reviewRequest && (
        <div className={`px-6 py-3 border-b border-gray-700 ${
          reviewStatus.reviewRequest.status === 'pending'
            ? 'bg-yellow-900/30 border-yellow-500/30'
            : 'bg-blue-900/30 border-blue-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  reviewStatus.reviewRequest.status === 'pending' ? 'bg-yellow-400' : 'bg-blue-400'
                }`}></div>
                <span className="font-medium">
                  {reviewStatus.isReviewer ? 'Review Mode' : 'Under Review'}
                </span>
              </div>
              <div className="text-sm text-gray-400">
                {reviewStatus.reviewRequest.title} - Status: {reviewStatus.reviewRequest.status.replace('_', ' ').toUpperCase()}
              </div>
            </div>

            {/* Reviewer Action Buttons */}
            {reviewStatus.isReviewer && reviewStatus.reviewRequest.status === 'in_review' && (
              <div className="flex gap-2">
                <button
                  onClick={() => handleReviewAction('approved')}
                  disabled={isProcessingReview}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  ✓ Approve
                </button>
                <button
                  onClick={() => handleReviewAction('requires_changes')}
                  disabled={isProcessingReview}
                  className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  ↻ Request Changes
                </button>
                <button
                  onClick={() => handleReviewAction('rejected')}
                  disabled={isProcessingReview}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  ✗ Reject
                </button>
              </div>
            )}

            {/* Read-only indicator for submitters */}
            {reviewStatus.isUnderReview && !reviewStatus.isReviewer && (
              <div className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-md">
                🔒 Read-only during review
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          {/* File Explorer Sidebar */}
          <Panel defaultSize={20} minSize={15} maxSize={40} className="border-r border-gray-700">
            <FileExplorer />
          </Panel>

          <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-500 transition-all duration-200 cursor-col-resize" />

          {/* Main Content Area */}
          <Panel defaultSize={80}>
            <PanelGroup direction="horizontal" className="h-full">
              {/* Editor Section */}
              <Panel defaultSize={60} minSize={30} className="border-r border-gray-700">
                <div className="h-full flex flex-col">
                  <div className="bg-gray-800 px-4 py-3 border-b border-gray-700/50 flex-shrink-0 flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <h2 className="text-sm font-medium text-gray-100">Editor</h2>
                    </div>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <CodeEditor
                      readOnly={reviewStatus.isUnderReview && !reviewStatus.isReviewer}
                      reviewMode={reviewStatus.isUnderReview}
                    />
                  </div>
                </div>
              </Panel>

              <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-500 transition-all duration-200 cursor-col-resize" />

              {/* Terminal Section */}
              <Panel defaultSize={40} minSize={25}>
                <div className="h-full flex flex-col">
                  <div className="bg-gray-800 px-4 py-3 border-b border-gray-700/50 flex-shrink-0 flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                      <h2 className="text-sm font-medium text-gray-100">Terminal</h2>
                    </div>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <Terminal />
                  </div>
                </div>
              </Panel>
            </PanelGroup>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}