'use client';

import { CodeEditor } from '../../../components/CodeEditor';
import { Terminal } from '../../../components/Terminal';
import { Header } from '../../../components/Header';
import { FileExplorer } from '../../../components/FileExplorer';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { useEffect, useState, use } from 'react';
import { useApp } from '../../../context/AppContext';
import { apiService } from '../../../services/api';
import { useAuth, useUserId } from '../../../contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

export default function WorkspacePage({ params: paramsPromise }: WorkspacePageProps) {
  const params = use(paramsPromise);
  const { state, setSession, setLoading, updateCode, setCurrentFile, setFiles, clearTerminal } = useApp();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const userId = useUserId();
  const router = useRouter();
  const [sessionLoadError, setSessionLoadError] = useState<string | null>(null);
  const [fastLoading, setFastLoading] = useState(false); // Show content as soon as session loads

  // Redirect to home if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, authLoading, router]);

  // Load session data
  useEffect(() => {
    const loadSession = async () => {
      if (!isAuthenticated || authLoading || !userId) return;
      
      try {
        setLoading(true);
        setSessionLoadError(null);
        
        // Clear terminal state when loading a new workspace
        // This ensures each workspace starts with a fresh terminal
        clearTerminal();
        
        // Use session UUID directly (no parsing needed)
        const sessionUuid = params.id;
        if (!sessionUuid || sessionUuid.trim() === '') {
          throw new Error(`Invalid session UUID: ${params.id}`);
        }
        
        // Only load session metadata from API - let WebSocket system handle files
        const sessionResponse = await apiService.getSession(sessionUuid, userId);
        
        // Convert API session to AppContext session format
        const session = {
          id: sessionResponse.data.id.toString(),
          userId: sessionResponse.data.user_id.toString(),
          code: '', // Will be populated by WebSocket system
          language: 'python' as const,
          createdAt: new Date(sessionResponse.data.created_at),
          updatedAt: new Date(sessionResponse.data.updated_at),
          isActive: true
        };
        
        // Set session in context - this will trigger WebSocket connection
        setSession(session);
        
        // Start container session and load workspace files from database
        try {
          await apiService.startContainerSession(sessionResponse.data.id);
          console.log('Container session started and workspace loaded');
        } catch (containerError) {
          console.warn('Failed to start container session:', containerError);
          // Continue anyway - container integration is optional
        }
        
        setFastLoading(true); // Enable fast loading to show UI immediately
        
        console.log('Session loaded, WebSocket will handle file loading');
        
      } catch (error) {
        console.error('Failed to load session:', error);
        setSessionLoadError(error instanceof Error ? error.message : 'Failed to load workspace');
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [params.id, isAuthenticated, authLoading, userId, clearTerminal]); // clearTerminal is stable from useCallback

  // Loading state - only show spinner if we don't have basic session data
  if (authLoading || (state.isLoading && !fastLoading && !state.currentSession)) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <div className="mb-4 text-xl">Loading workspace...</div>
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
          <div className="mb-4 text-xl text-red-400">Failed to load workspace</div>
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