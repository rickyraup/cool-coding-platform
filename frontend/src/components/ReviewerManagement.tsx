'use client';

import { useState, useEffect } from 'react';
import { apiService, type User } from '../services/api';

interface ReviewerManagementProps {
  currentUser?: User;
  onUserUpdate?: (user: User) => void;
}

export function ReviewerManagement({ currentUser, onUserUpdate }: ReviewerManagementProps): JSX.Element {
  const [reviewers, setReviewers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  // Load reviewers on component mount
  useEffect(() => {
    loadReviewers();
  }, []);

  const loadReviewers = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getReviewers();
      setReviewers(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reviewers');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleReviewerStatus = async (isReviewer: boolean, level: number = 1): Promise<void> => {
    try {
      setUpdating(true);
      setError(null);

      const response = await apiService.toggleReviewerStatus(isReviewer, level);

      // Update local state
      if (onUserUpdate) {
        onUserUpdate(response.user);
      }

      // Reload reviewers list to reflect changes
      await loadReviewers();

      alert(response.message);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update reviewer status');
    } finally {
      setUpdating(false);
    }
  };

  const getReviewerLevelText = (level: number): string => {
    switch (level) {
      case 0: return 'Regular User';
      case 1: return 'Junior Reviewer';
      case 2: return 'Senior Reviewer';
      default: return 'Unknown';
    }
  };

  const getReviewerLevelColor = (level: number): string => {
    switch (level) {
      case 0: return 'text-gray-400';
      case 1: return 'text-blue-400';
      case 2: return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-600 pb-4">
        <h2 className="text-2xl font-bold text-white">Reviewer Management</h2>
        <p className="text-gray-400 mt-2">
          Manage your reviewer status and view available reviewers for code reviews.
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Current User Status */}
      {currentUser && (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Your Reviewer Status</h3>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-white">
                <span className="font-medium">{currentUser.username}</span>
                <span className="ml-2 text-gray-400">({currentUser.email})</span>
              </p>
              <p className={`text-sm mt-1 ${getReviewerLevelColor(currentUser.reviewer_level || 0)}`}>
                {currentUser.is_reviewer ? getReviewerLevelText(currentUser.reviewer_level || 1) : 'Not a reviewer'}
              </p>
            </div>

            <div className="flex space-x-3">
              {!currentUser.is_reviewer ? (
                <>
                  <button
                    onClick={() => handleToggleReviewerStatus(true, 1)}
                    disabled={updating}
                    className="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? 'Updating...' : 'Become Junior Reviewer'}
                  </button>
                  <button
                    onClick={() => handleToggleReviewerStatus(true, 2)}
                    disabled={updating}
                    className="px-4 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? 'Updating...' : 'Become Senior Reviewer'}
                  </button>
                </>
              ) : (
                <>
                  {currentUser.reviewer_level === 1 && (
                    <button
                      onClick={() => handleToggleReviewerStatus(true, 2)}
                      disabled={updating}
                      className="px-4 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {updating ? 'Updating...' : 'Upgrade to Senior'}
                    </button>
                  )}
                  <button
                    onClick={() => handleToggleReviewerStatus(false, 0)}
                    disabled={updating}
                    className="px-4 py-2 text-sm font-medium bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? 'Updating...' : 'Stop Being Reviewer'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Available Reviewers */}
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Available Reviewers</h3>
          <button
            onClick={loadReviewers}
            disabled={loading}
            className="px-3 py-1.5 text-sm font-medium bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-md transition-colors disabled:opacity-50"
          >
            {loading ? 'Loading...' : '🔄 Refresh'}
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="text-gray-400 mt-2">Loading reviewers...</p>
          </div>
        ) : reviewers.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-400">No reviewers available yet.</p>
            <p className="text-gray-500 text-sm mt-1">Be the first to become a reviewer!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reviewers.map((reviewer) => (
              <div
                key={reviewer.id}
                className="flex items-center justify-between bg-gray-700 rounded-lg p-4"
              >
                <div>
                  <p className="text-white font-medium">{reviewer.username}</p>
                  <p className="text-gray-400 text-sm">{reviewer.email}</p>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                    reviewer.reviewer_level === 2
                      ? 'bg-purple-500/20 text-purple-300'
                      : 'bg-blue-500/20 text-blue-300'
                  }`}>
                    {getReviewerLevelText(reviewer.reviewer_level || 1)}
                  </span>
                  <p className="text-gray-500 text-xs mt-1">
                    Joined {new Date(reviewer.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
        <h4 className="text-blue-300 font-medium mb-2">📝 About Reviewer Levels</h4>
        <div className="text-blue-200 text-sm space-y-1">
          <p><span className="font-medium">Junior Reviewer:</span> Can review code and provide feedback</p>
          <p><span className="font-medium">Senior Reviewer:</span> Can review code and mentor junior reviewers</p>
          <p><span className="font-medium">How it works:</span> Anyone can become a reviewer and others can choose you to review their code submissions</p>
        </div>
      </div>
    </div>
  );
}