'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { ReviewerManagement } from '../../components/ReviewerManagement';
import { apiService, type User } from '../../services/api';

export default function ReviewersPage(): JSX.Element {
  const { isAuthenticated, user: authUser } = useAuth();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadCurrentUser();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const loadCurrentUser = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      const user = await apiService.getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user info');
    } finally {
      setLoading(false);
    }
  };

  const handleUserUpdate = (updatedUser: User): void => {
    setCurrentUser(updatedUser);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="container mx-auto px-6 py-16">
          <div className="max-w-md mx-auto bg-gray-800 border border-gray-600 rounded-lg p-6 text-center">
            <h1 className="text-2xl font-bold text-white mb-4">Authentication Required</h1>
            <p className="text-gray-400 mb-6">
              You need to be logged in to manage your reviewer status.
            </p>
            <button
              onClick={() => window.location.href = '/'}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="container mx-auto px-6 py-16">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="text-gray-400 mt-4">Loading your reviewer information...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="container mx-auto px-6 py-16">
          <div className="max-w-md mx-auto bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
            <h1 className="text-2xl font-bold text-red-300 mb-4">Error</h1>
            <p className="text-red-400 mb-6">{error}</p>
            <div className="space-x-3">
              <button
                onClick={loadCurrentUser}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <ReviewerManagement
            currentUser={currentUser || undefined}
            onUserUpdate={handleUserUpdate}
          />
        </div>
      </div>
    </div>
  );
}