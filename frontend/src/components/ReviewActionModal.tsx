'use client';

import { useState } from 'react';

interface ReviewActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (action: 'approved' | 'rejected', notes?: string) => Promise<void>;
  reviewTitle: string;
}

export function ReviewActionModal({ isOpen, onClose, onSubmit, reviewTitle }: ReviewActionModalProps) {
  const [selectedAction, setSelectedAction] = useState<'approved' | 'rejected' | null>(null);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!selectedAction) return;

    try {
      setIsSubmitting(true);
      await onSubmit(selectedAction, notes.trim() || undefined);
      onClose();
      // Reset form
      setSelectedAction(null);
      setNotes('');
    } catch (error) {
      console.error('Failed to submit review action:', error);
      // Error is handled by parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setSelectedAction(null);
      setNotes('');
      onClose();
    }
  };

  if (!isOpen) return null;

  const getActionButtonStyle = (action: string) => {
    const baseStyle = "flex-1 p-4 border-2 rounded-lg transition-all cursor-pointer text-center";
    const isSelected = selectedAction === action;

    switch (action) {
      case 'approved':
        return `${baseStyle} ${isSelected
          ? 'border-green-500 bg-green-500/20 text-green-300'
          : 'border-gray-600 hover:border-green-500/50 text-gray-300 hover:text-green-300'}`;
      case 'rejected':
        return `${baseStyle} ${isSelected
          ? 'border-red-500 bg-red-500/20 text-red-300'
          : 'border-gray-600 hover:border-red-500/50 text-gray-300 hover:text-red-300'}`;
      default:
        return baseStyle;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-75"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 border border-gray-700">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">Review Action</h3>
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="mb-6">
            <div className="text-sm text-gray-400 mb-2">Review:</div>
            <div className="text-white font-medium">{reviewTitle}</div>
          </div>

          {/* Action Selection */}
          <div className="mb-6">
            <div className="text-sm font-medium text-gray-300 mb-3">Select Action:</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                className={getActionButtonStyle('approved')}
                onClick={() => setSelectedAction('approved')}
              >
                <div className="text-2xl mb-2">✅</div>
                <div className="font-medium">Approve</div>
                <div className="text-xs opacity-75">Accept the changes</div>
              </div>

              <div
                className={getActionButtonStyle('rejected')}
                onClick={() => setSelectedAction('rejected')}
              >
                <div className="text-2xl mb-2">❌</div>
                <div className="font-medium">Reject</div>
                <div className="text-xs opacity-75">Decline the submission</div>
              </div>
            </div>
          </div>

          {/* Notes Section */}
          <div className="mb-6">
            <label htmlFor="review-notes" className="block text-sm font-medium text-gray-300 mb-2">
              Notes (Optional)
            </label>
            <textarea
              id="review-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any feedback or comments..."
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
              disabled={isSubmitting}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!selectedAction || isSubmitting}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Review'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}