'use client';

import { useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { CodeEditor } from './CodeEditor';
import { FileExplorer } from './FileExplorer';
import { useApp } from '../contexts/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

interface ReviewerWorkspaceProps {
  reviewRequest: {
    id: number;
    title: string;
    status: string;
  };
  onReviewAction: () => void;
}

export function ReviewerWorkspace({ reviewRequest, onReviewAction }: ReviewerWorkspaceProps) {
  const { state } = useApp();
  const { sendTerminalCommand } = useWebSocket();
  const [executionOutput, setExecutionOutput] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);

  const handleRunFile = async (fileName: string) => {
    if (!fileName.endsWith('.py')) return;

    setIsExecuting(true);
    setExecutionOutput(prev => prev + `\n$ python ${fileName}\n`);

    try {
      const success = sendTerminalCommand(`python ${fileName}`);
      if (!success) {
        setExecutionOutput(prev => prev + 'Error: Failed to execute file\n');
      }
    } catch (error) {
      setExecutionOutput(prev => prev + `Error: ${error}\n`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="flex-1 overflow-hidden">
      <PanelGroup direction="horizontal" className="h-full">
        {/* File Explorer Sidebar */}
        <Panel defaultSize={25} minSize={20} maxSize={40} className="border-r border-gray-700">
          <div className="h-full flex flex-col">
            <div className="bg-gray-800 px-4 py-3 border-b border-gray-700/50 flex-shrink-0 flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <h2 className="text-sm font-medium text-gray-100">Files</h2>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              <FileExplorer
                onRunFile={handleRunFile}
                reviewMode={true}
                showRunButtons={true}
              />
            </div>
          </div>
        </Panel>

        <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-500 transition-all duration-200 cursor-col-resize" />

        {/* Main Content Area */}
        <Panel defaultSize={75}>
          <PanelGroup direction="horizontal" className="h-full">
            {/* Editor Section - Read Only */}
            <Panel defaultSize={60} minSize={30} className="border-r border-gray-700">
              <div className="h-full flex flex-col">
                <div className="bg-gray-800 px-4 py-3 border-b border-gray-700/50 flex-shrink-0 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <h2 className="text-sm font-medium text-gray-100">Code Review</h2>
                    </div>
                    <div className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded">
                      Read Only
                    </div>
                  </div>

                  {/* Review Action Button */}
                  {reviewRequest.status === 'in_review' ? (
                    <button
                      onClick={onReviewAction}
                      className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-md text-sm font-medium transition-all duration-200"
                    >
                      📝 Review Workspace
                    </button>
                  ) : (
                    <div className="px-4 py-2 rounded-md text-sm font-medium">
                      {reviewRequest.status === 'approved' ? (
                        <span className="text-green-400 bg-green-900/30 px-3 py-1 rounded">
                          ✅ Approved
                        </span>
                      ) : reviewRequest.status === 'rejected' ? (
                        <span className="text-red-400 bg-red-900/30 px-3 py-1 rounded">
                          ❌ Rejected
                        </span>
                      ) : (
                        <span className="text-yellow-400 bg-yellow-900/30 px-3 py-1 rounded">
                          📋 {reviewRequest.status.replace('_', ' ').toUpperCase()}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex-1 overflow-hidden">
                  <CodeEditor readOnly={true} reviewMode={true} />
                </div>
              </div>
            </Panel>

            <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-500 transition-all duration-200 cursor-col-resize" />

            {/* Output Section - Instead of Terminal */}
            <Panel defaultSize={40} minSize={25}>
              <div className="h-full flex flex-col">
                <div className="bg-gray-800 px-4 py-3 border-b border-gray-700/50 flex-shrink-0 flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                    <h2 className="text-sm font-medium text-gray-100">Execution Output</h2>
                  </div>
                  <button
                    onClick={() => setExecutionOutput('')}
                    className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded border border-gray-600 hover:border-gray-500 transition-colors"
                  >
                    Clear
                  </button>
                </div>
                <div className="flex-1 overflow-hidden bg-gray-900 relative">
                  {executionOutput ? (
                    <div className="h-full overflow-auto p-4">
                      <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                        {executionOutput}
                      </pre>
                      {isExecuting && (
                        <div className="flex items-center gap-2 mt-2 text-blue-400">
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                          <span className="text-sm">Executing...</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-gray-500">
                      <div className="text-center">
                        <div className="text-4xl mb-4">▶️</div>
                        <div className="text-sm">Click the play buttons to run files</div>
                        <div className="text-xs text-gray-600 mt-1">Output will appear here</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Panel>
          </PanelGroup>
        </Panel>
      </PanelGroup>
    </div>
  );
}