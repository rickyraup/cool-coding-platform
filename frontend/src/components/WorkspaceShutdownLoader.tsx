'use client';

import { useEffect, useState } from 'react';

interface WorkspaceShutdownLoaderProps {
  isVisible: boolean;
  message?: string;
}

export default function WorkspaceShutdownLoader({ isVisible, message = "Shutting down workspace..." }: WorkspaceShutdownLoaderProps) {
  const [dots, setDots] = useState("");
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    "Saving workspace files...",
    "Stopping container...",
    "Cleaning up resources...",
    "Finalizing shutdown..."
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
    }, 500);

    // Cycle through steps
    const stepsInterval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % steps.length);
    }, 1500);

    return () => {
      clearInterval(dotsInterval);
      clearInterval(stepsInterval);
    };
  }, [isVisible, steps.length]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          {/* Loading spinner */}
          <div className="mb-6 flex justify-center">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
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
              className="bg-blue-500 h-2 rounded-full transition-all duration-1500 ease-in-out"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            ></div>
          </div>

          {/* Info message */}
          <p className="text-sm text-gray-400">
            Please wait while we safely close your workspace...
          </p>
        </div>
      </div>
    </div>
  );
}