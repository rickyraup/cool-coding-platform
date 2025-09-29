'use client';

import { useEffect, useState } from 'react';

interface WorkspaceStartupLoaderProps {
  isVisible: boolean;
  message?: string;
}

export default function WorkspaceStartupLoader({ isVisible, message = "Starting up workspace..." }: WorkspaceStartupLoaderProps) {
  const [dots, setDots] = useState("");
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    "Initializing container...",
    "Loading workspace files...",
    "Setting up environment...",
    "Connecting services...",
    "Ready to code!"
  ];

  useEffect(() => {
    if (!isVisible) {
      setDots("");
      setCurrentStep(0);
      return;
    }

    // Animate dots
    const dotsInterval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return "";
        return prev + ".";
      });
    }, 400);

    // Cycle through steps
    const stepsInterval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % steps.length);
    }, 1200);

    return () => {
      clearInterval(dotsInterval);
      clearInterval(stepsInterval);
    };
  }, [isVisible, steps.length]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/90 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          {/* Loading spinner */}
          <div className="mb-6 flex justify-center">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-gray-600 border-t-green-500 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Main message */}
          <h2 className="text-xl font-semibold text-white mb-2">
            {message}
          </h2>

          {/* Current step with animated dots */}
          <p className="text-gray-300 mb-4">
            {steps[currentStep]}{dots}
          </p>

          {/* Progress bar */}
          <div className="w-full bg-gray-700 rounded-full h-2 mb-4">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-1200 ease-in-out"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            ></div>
          </div>

          {/* Info message */}
          <p className="text-sm text-gray-400">
            Please wait while we prepare your development environment...
          </p>
        </div>
      </div>
    </div>
  );
}