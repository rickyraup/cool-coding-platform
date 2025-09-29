'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface User {
  id: number;
  username: string;
  email: string;
  is_reviewer: boolean;
  reviewer_level: number;
  created_at?: string;
}

interface ReviewSubmissionModalProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; description: string; priority: string; reviewer_ids: number[] }) => Promise<void>;
}

export function ReviewSubmissionModal({ sessionId, isOpen, onClose, onSubmit }: ReviewSubmissionModalProps): JSX.Element | null {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium');
  const [selectedReviewers, setSelectedReviewers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search users for reviewer selection
  useEffect(() => {
    const searchUsers = async () => {
      if (searchQuery.length >= 2) {
        setIsSearching(true);
        try {
          const response = await apiService.searchUsers(searchQuery);
          setSearchResults(response.data);
        } catch (err) {
          console.error('Failed to search users:', err);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
      }
    };

    const timeoutId = setTimeout(searchUsers, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      await onSubmit({
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        reviewer_ids: selectedReviewers.map(r => r.id)
      });
      
      // Reset form and close modal
      setTitle('');
      setDescription('');
      setPriority('medium');
      setSelectedReviewers([]);
      setSearchQuery('');
      setSearchResults([]);
      onClose();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review request');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = (): void => {
    if (!isSubmitting) {
      setTitle('');
      setDescription('');
      setPriority('medium');
      setSelectedReviewers([]);
      setSearchQuery('');
      setSearchResults([]);
      setError(null);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-800 border border-gray-600 rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-600">
          <h2 className="text-lg font-semibold text-white">Submit for Review</h2>
          <p className="text-sm text-gray-400 mt-1">
            Request a code review for session {sessionId.substring(0, 8)}...
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-2">
              Review Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Review my data analysis script"
              disabled={isSubmitting}
              maxLength={255}
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">
              Description (optional)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              placeholder="Provide additional context about what you'd like reviewed..."
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-300 mb-2">
              Priority
            </label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high' | 'urgent')}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSubmitting}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div>
            <label htmlFor="reviewers" className="block text-sm font-medium text-gray-300 mb-2">
              Reviewers (optional)
            </label>

            {/* Selected reviewers */}
            {selectedReviewers.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {selectedReviewers.map((reviewer) => (
                  <span
                    key={reviewer.id}
                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-900 text-blue-200"
                  >
                    {reviewer.username}
                    <button
                      type="button"
                      onClick={() => setSelectedReviewers(prev => prev.filter(r => r.id !== reviewer.id))}
                      className="ml-1 text-blue-400 hover:text-blue-300"
                      disabled={isSubmitting}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Search input */}
            <input
              type="text"
              id="reviewers"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Search for users by username or email..."
              disabled={isSubmitting}
            />

            {/* Search results */}
            {searchResults.length > 0 && (
              <div className="mt-2 bg-gray-700 border border-gray-600 rounded-lg max-h-40 overflow-y-auto">
                {searchResults.map((user) => (
                  <button
                    key={user.id}
                    type="button"
                    onClick={() => {
                      if (!selectedReviewers.find(r => r.id === user.id)) {
                        setSelectedReviewers(prev => [...prev, user]);
                      }
                      setSearchQuery('');
                      setSearchResults([]);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-600 flex items-center justify-between text-sm"
                    disabled={isSubmitting || selectedReviewers.find(r => r.id === user.id) !== undefined}
                  >
                    <span className="text-white">{user.username}</span>
                    <div className="flex items-center space-x-2">
                      {user.is_reviewer && (
                        <span className="text-xs text-green-400">Reviewer</span>
                      )}
                      <span className="text-xs text-gray-400">{user.email}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {isSearching && (
              <div className="mt-2 text-sm text-gray-400">Searching...</div>
            )}
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 text-sm font-medium bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting || !title.trim()}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}