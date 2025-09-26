'use client';

import { CodeEditor } from '../../../../components/CodeEditor';
import { Terminal } from '../../../../components/Terminal';
import { Header } from '../../../../components/Header';
import { FileExplorer } from '../../../../components/FileExplorer';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { useEffect, useState } from 'react';
import { useApp } from '../../../../context/AppContext';
import { useRouter, useParams } from 'next/navigation';

export default function GuestWorkspacePage() {
  const params = useParams();
  const { state, setSession, setLoading, updateCode, setCurrentFile } = useApp();
  const router = useRouter();
  const [guestLoadError, setGuestLoadError] = useState<string | null>(null);

  // Initialize guest session
  useEffect(() => {
    const initGuestSession = async () => {
      try {
        setLoading(true);
        setGuestLoadError(null);
        
        const guestId = Array.isArray(params.id) ? params.id[0] : params.id;
        const storedGuestMode = localStorage.getItem('guestMode');
        const storedGuestId = localStorage.getItem('guestId');
        
        // Verify this is a valid guest session
        if (!storedGuestMode || storedGuestId !== guestId) {
          throw new Error('Invalid or expired guest session');
        }

        // Create a guest session object
        const guestSession = {
          id: guestId,
          userId: 'guest',
          code: '# Welcome to Coding Workspaces Project Guest Mode!\n# Your session is temporary and will be lost when you close the browser.\n\nprint("Hello, Guest!")\n\n# Try writing some Python code here:',
          language: 'python' as const,
          createdAt: new Date(),
          updatedAt: new Date(),
          isActive: true
        };
        
        setSession(guestSession);
        updateCode(guestSession.code);
        setCurrentFile('main.py');
        
      } catch (error) {
        console.error('Failed to initialize guest session:', error);
        setGuestLoadError(error instanceof Error ? error.message : 'Failed to initialize guest session');
      } finally {
        setLoading(false);
      }
    };

    initGuestSession();
  }, [params.id, setSession, setLoading, updateCode, setCurrentFile]);

  // Loading state
  if (state.isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <div className="mb-4 text-xl">Initializing guest workspace...</div>
          <div className="text-gray-400">Please wait</div>
        </div>
      </div>
    );
  }

  // Error state
  if (guestLoadError) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <div className="mb-4 text-xl text-red-400">Failed to load guest workspace</div>
          <div className="mb-6 text-gray-400">{guestLoadError}</div>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900 text-white overflow-hidden">
      {/* Guest Mode Header with warning */}
      <div className="bg-yellow-900/20 border-b border-yellow-500/20 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-yellow-400">⚠️</span>
          <span className="text-yellow-300 text-sm font-medium">Guest Mode</span>
          <span className="text-gray-400 text-sm">• Session is temporary • Sign up to save your work</span>
        </div>
        <button
          onClick={() => router.push('/')}
          className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded transition-colors"
        >
          Sign Up / Login
        </button>
      </div>
      
      <Header />
      
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
                      <span className="text-xs text-yellow-400 bg-yellow-500/10 px-2 py-1 rounded">Guest</span>
                    </div>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <CodeEditor />
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
                      <span className="text-xs text-yellow-400 bg-yellow-500/10 px-2 py-1 rounded">Guest</span>
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