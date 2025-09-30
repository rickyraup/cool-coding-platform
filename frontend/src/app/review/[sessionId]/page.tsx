'use client';

import { Header } from '../../../components/Header';
import { ReviewerWorkspace } from '../../../components/ReviewerWorkspace';
import { useEffect, useState, use } from 'react';
import { useApp } from '../../../contexts/AppContext';
import { apiService, type ReviewRequest } from '../../../services/api';
import { getWorkspaceFiles, getFileContent, getWorkspaceStatus, ensureDefaultFiles } from '../../../services/workspaceApi';
import WorkspaceStartupLoader from '../../../components/WorkspaceStartupLoader';
import { useAuth, useUserId } from '../../../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { ReviewActionModal } from '../../../components/ReviewActionModal';

interface ReviewPageProps {
  params: Promise<{ sessionId: string }>;
}

export default function ReviewPage({ params: paramsPromise }: ReviewPageProps) {
  const params = use(paramsPromise);
  const { state, setSession, setLoading, updateCode, setCurrentFile, setFiles, clearTerminal } = useApp();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const userId = useUserId();
  const router = useRouter();
  const [sessionLoadError, setSessionLoadError] = useState<string | null>(null);
  const [fastLoading, setFastLoading] = useState(false);
  const [workspaceInitialized, setWorkspaceInitialized] = useState(false);
  const [showStartupLoader, setShowStartupLoader] = useState(true);
  const [reviewRequest, setReviewRequest] = useState<ReviewRequest | null>(null);
  const [isProcessingReview, setIsProcessingReview] = useState(false);
  const [showReviewActionModal, setShowReviewActionModal] = useState(false);

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

      const sessionUuid = params.sessionId;
      if (!sessionUuid || sessionUuid.trim() === '') return;

      try {
        const checkStatus = async (): Promise<boolean> => {
          const status = await getWorkspaceStatus(sessionUuid);

          if (status.status === 'ready' && status.initialized) {
            setWorkspaceInitialized(true);
            setShowStartupLoader(false);
            return true;
          } else if (status.status === 'empty') {
            await ensureDefaultFiles(sessionUuid);
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
          const pollInterval = setInterval(async () => {
            const ready = await checkStatus();
            if (ready) {
              clearInterval(pollInterval);
            }
          }, 1000);

          return () => clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Failed to check workspace status:', error);
        setSessionLoadError('Failed to initialize workspace');
        setShowStartupLoader(false);
      }
    };

    checkWorkspaceStatus();
  }, [params.sessionId, isAuthenticated, authLoading, userId]);

  // Load session data and review request
  useEffect(() => {
    const loadSession = async () => {
      if (!isAuthenticated || authLoading || !userId || !workspaceInitialized) return;

      try {
        setLoading(true);
        setSessionLoadError(null);

        clearTerminal();

        const sessionUuid = params.sessionId;
        if (!sessionUuid || sessionUuid.trim() === '') {
          throw new Error(`Invalid session UUID: ${params.sessionId}`);
        }

        // Load session metadata from API
        const sessionResponse = await apiService.getSession(sessionUuid, userId);

        // Convert API session to AppContext session format
        const session = {
          id: sessionResponse.data.id.toString(),
          userId: sessionResponse.data.user_id.toString(),
          code: '',
          language: 'python' as const,
          createdAt: new Date(sessionResponse.data.created_at),
          updatedAt: new Date(sessionResponse.data.updated_at),
          isActive: true
        };

        setSession(session);

        // Load workspace files
        try {

          let files = await getWorkspaceFiles(sessionUuid);

          setFiles(files);

          // Auto-select main.py if it exists
          const mainFile = files.find(file => file.name === 'main.py');
          if (mainFile) {
            setCurrentFile(mainFile.path);

            const fileContent = await getFileContent(sessionUuid, mainFile.name);
            updateCode(fileContent.content);
          }

        } catch (fileError) {
          console.error('Failed to load workspace files:', fileError);
          setSessionLoadError('Failed to load workspace files');
        }

        // Load review request for this session
        try {
          const reviewStatus = await apiService.getReviewStatusForSession(sessionUuid);
          if (reviewStatus.reviewRequest) {
            setReviewRequest(reviewStatus.reviewRequest);

            // Check if user is actually a reviewer for this request
            if (!reviewStatus.isReviewer) {
              setSessionLoadError('You are not authorized to review this workspace');
              return;
            }

            // Auto-transition from pending to in_review when reviewer accesses
            if (reviewStatus.reviewRequest.status === 'pending') {
              try {
                await apiService.updateReviewStatus(reviewStatus.reviewRequest.id, 'in_review');
                const updatedRequest = { ...reviewStatus.reviewRequest, status: 'in_review' as const };
                setReviewRequest(updatedRequest);
              } catch (updateError) {
                console.error('Failed to update review status to in_review:', updateError);
              }
            }
          } else {
            setSessionLoadError('No review request found for this session');
          }
        } catch (error) {
          console.error('Failed to load review request:', error);
          setSessionLoadError('Failed to load review request');
        }

        setFastLoading(true);

      } catch (error) {
        console.error('Failed to load session:', error);
        setSessionLoadError(error instanceof Error ? error.message : 'Failed to load workspace');
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [params.sessionId, isAuthenticated, authLoading, userId, workspaceInitialized, clearTerminal]);

  // Handler for reviewer actions
  const handleReviewAction = async (action: 'approved' | 'rejected', _notes?: string) => {
    if (!reviewRequest) return;

    // Prevent actions on already completed reviews
    if (reviewRequest.status === 'approved' || reviewRequest.status === 'rejected') {
      console.warn('Cannot perform action on completed review:', reviewRequest.status);
      return;
    }

    try {
      setIsProcessingReview(true);
      await apiService.updateReviewStatus(reviewRequest.id, action);

      // Show success message
      const actionText = action.replace('_', ' ').toLowerCase();
      alert(`Review ${actionText} successfully!`);

      // Redirect to reviews dashboard
      router.push('/reviews');

    } catch (error) {
      console.error('Failed to update review status:', error);
      throw error;
    } finally {
      setIsProcessingReview(false);
    }
  };

  // Show startup loader while workspace is initializing
  if (showStartupLoader) {
    return <WorkspaceStartupLoader isVisible={true} message="Starting up review workspace..." />;
  }

  // Loading state
  if (authLoading || (state.isLoading && !fastLoading && !state.currentSession)) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <div className="mb-4 text-xl">Loading review workspace...</div>
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
          <div className="mb-4 text-xl text-red-400">Failed to load review workspace</div>
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
      {reviewRequest && (
        <div className="px-6 py-3 border-b border-gray-700 bg-blue-900/30 border-blue-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-400"></div>
                <span className="font-medium">Review Mode</span>
              </div>
              <div className="text-sm text-gray-400">
                {reviewRequest.title} - Status: {reviewRequest.status.replace('_', ' ').toUpperCase()}
              </div>
            </div>

            {/* Review Action Button */}
            {reviewRequest.status === 'in_review' && (
              <button
                onClick={() => setShowReviewActionModal(true)}
                disabled={isProcessingReview}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                📝 Review Workspace
              </button>
            )}

            {/* Show status for completed reviews */}
            {(reviewRequest.status === 'approved' || reviewRequest.status === 'rejected') && (
              <div className="px-4 py-2 rounded-md text-sm font-medium">
                {reviewRequest.status === 'approved' ? (
                  <span className="text-green-400 bg-green-900/30 px-3 py-1 rounded">
                    ✅ Review Completed - Approved
                  </span>
                ) : (
                  <span className="text-red-400 bg-red-900/30 px-3 py-1 rounded">
                    ❌ Review Completed - Rejected
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        {reviewRequest ? (
          <ReviewerWorkspace
            reviewRequest={reviewRequest}
            onReviewAction={() => setShowReviewActionModal(true)}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-xl text-gray-400 mb-4">Loading review...</div>
            </div>
          </div>
        )}
      </div>

      {/* Review Action Modal */}
      {showReviewActionModal && reviewRequest && reviewRequest.status === 'in_review' && (
        <ReviewActionModal
          isOpen={showReviewActionModal}
          onClose={() => setShowReviewActionModal(false)}
          onSubmit={handleReviewAction}
          reviewTitle={reviewRequest.title}
        />
      )}
    </div>
  );
}