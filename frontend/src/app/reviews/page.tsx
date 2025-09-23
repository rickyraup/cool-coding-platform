'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { apiService, type ReviewRequest } from '../../services/api';
import { Header } from '../../components/Header';

interface ReviewStats {
  total_pending: number;
  total_in_review: number;
  total_approved: number;
  total_rejected: number;
  my_pending_reviews: number;
  my_assigned_reviews: number;
}

export default function ReviewsPage(): JSX.Element {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [myRequests, setMyRequests] = useState<ReviewRequest[]>([]);
  const [assignedReviews, setAssignedReviews] = useState<ReviewRequest[]>([]);
  const [activeTab, setActiveTab] = useState<'my-requests' | 'assigned'>('my-requests');

  // Redirect to home if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, authLoading, router]);

  // Load review data
  useEffect(() => {
    const loadReviewData = async (): Promise<void> => {
      if (!isAuthenticated || authLoading) return;

      try {
        setIsLoading(true);
        setError(null);

        // Load overview stats
        const overviewPromise = apiService.getReviewOverview();
        
        // Load my review requests
        const myRequestsPromise = apiService.getMyReviewRequests();
        
        // Load assigned reviews
        const assignedPromise = apiService.getAssignedReviews();

        const [overviewResponse, myRequestsResponse, assignedResponse] = await Promise.all([
          overviewPromise,
          myRequestsPromise,
          assignedPromise
        ]);

        setStats(overviewResponse);
        setMyRequests(myRequestsResponse.data);
        setAssignedReviews(assignedResponse.data);

      } catch (err) {
        console.error('Failed to load review data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load reviews');
      } finally {
        setIsLoading(false);
      }
    };

    loadReviewData();
  }, [isAuthenticated, authLoading]);

  // Loading state
  if (authLoading || isLoading) {
    return (
      <div className="h-screen w-screen flex flex-col bg-gray-900 text-white">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="mb-4 text-xl">Loading reviews...</div>
            <div className="text-gray-400">Please wait</div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-screen w-screen flex flex-col bg-gray-900 text-white">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="mb-4 text-xl text-red-400">Failed to load reviews</div>
            <div className="mb-6 text-gray-400">{error}</div>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return null;
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'pending': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'in_review': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'approved': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'rejected': return 'bg-red-500/20 text-red-300 border-red-500/30';
      case 'requires_changes': return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'urgent': return 'bg-red-500/20 text-red-300 border-red-500/30';
      case 'high': return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
      case 'medium': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'low': return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900 text-white">
      <Header />
      
      <div className="flex-1 overflow-hidden p-6">
        <div className="max-w-7xl mx-auto h-full flex flex-col">
          {/* Page Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-white mb-2">Code Reviews</h1>
            <p className="text-gray-400">Manage your review requests and assignments</p>
          </div>

          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-2xl font-bold text-yellow-400">{stats.total_pending}</div>
                <div className="text-sm text-gray-400">Pending</div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-400">{stats.total_in_review}</div>
                <div className="text-sm text-gray-400">In Review</div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-400">{stats.total_approved}</div>
                <div className="text-sm text-gray-400">Approved</div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-2xl font-bold text-red-400">{stats.total_rejected}</div>
                <div className="text-sm text-gray-400">Rejected</div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-2xl font-bold text-purple-400">{stats.my_pending_reviews}</div>
                <div className="text-sm text-gray-400">My Requests</div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="text-2xl font-bold text-indigo-400">{stats.my_assigned_reviews}</div>
                <div className="text-sm text-gray-400">Assigned to Me</div>
              </div>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex space-x-1 mb-6 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('my-requests')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'my-requests'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              My Requests ({myRequests.length})
            </button>
            <button
              onClick={() => setActiveTab('assigned')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'assigned'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              Assigned to Me ({assignedReviews.length})
            </button>
          </div>

          {/* Reviews List */}
          <div className="flex-1 overflow-auto">
            {activeTab === 'my-requests' ? (
              <div className="space-y-4">
                {myRequests.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">No review requests found</div>
                    <p className="text-gray-500 text-sm">Submit a workspace for review to get started</p>
                  </div>
                ) : (
                  myRequests.map((request) => (
                    <div key={request.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-white mb-2">{request.title}</h3>
                          {request.description && (
                            <p className="text-gray-400 text-sm mb-3">{request.description}</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-3 ml-4">
                          <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getStatusColor(request.status)}`}>
                            {request.status.replace('_', ' ').toUpperCase()}
                          </span>
                          <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getPriorityColor(request.priority)}`}>
                            {request.priority.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm text-gray-400">
                        <div className="flex items-center space-x-4">
                          <span>Session: {request.session_id}</span>
                          <span>Submitted: {formatDate(request.created_at)}</span>
                          {request.assigned_to && (
                            <span>Reviewer: User {request.assigned_to}</span>
                          )}
                        </div>
                        <button
                          onClick={() => router.push(`/workspace/${request.session_id}`)}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          View Workspace →
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {assignedReviews.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">No reviews assigned</div>
                    <p className="text-gray-500 text-sm">Reviews assigned to you will appear here</p>
                  </div>
                ) : (
                  assignedReviews.map((request) => (
                    <div key={request.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-white mb-2">{request.title}</h3>
                          {request.description && (
                            <p className="text-gray-400 text-sm mb-3">{request.description}</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-3 ml-4">
                          <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getStatusColor(request.status)}`}>
                            {request.status.replace('_', ' ').toUpperCase()}
                          </span>
                          <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getPriorityColor(request.priority)}`}>
                            {request.priority.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm text-gray-400">
                        <div className="flex items-center space-x-4">
                          <span>Session: {request.session_id}</span>
                          <span>Submitted: {formatDate(request.created_at)}</span>
                          <span>By: User {request.submitted_by}</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <button
                            onClick={() => router.push(`/workspace/${request.session_id}`)}
                            className="text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            Review →
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}