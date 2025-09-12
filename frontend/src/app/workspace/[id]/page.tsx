'use client';

import { CodeEditor } from '../../../components/CodeEditor';
import { Terminal } from '../../../components/Terminal';
import { Header } from '../../../components/Header';
import { FileExplorer } from '../../../components/FileExplorer';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { useEffect, useState, use } from 'react';
import { useApp } from '../../../context/AppContext';
import { apiService } from '../../../services/api';
import { useAuth } from '../../../contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

export default function WorkspacePage({ params: paramsPromise }: WorkspacePageProps) {
  const params = use(paramsPromise);
  const { state, setSession, setLoading, setError, updateCode } = useApp();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [sessionLoadError, setSessionLoadError] = useState<string | null>(null);

  // Redirect to home if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, authLoading, router]);

  // Load session data
  useEffect(() => {
    const loadSession = async () => {
      if (!isAuthenticated || authLoading) return;
      
      try {
        setLoading(true);
        setSessionLoadError(null);
        
        // Parse session ID
        const sessionId = parseInt(params.id, 10);
        if (isNaN(sessionId) || sessionId <= 0) {
          throw new Error(`Invalid session ID: ${params.id}`);
        }
        
        // Load session from API
        const response = await apiService.getSession(sessionId);
        
        // Convert API session to AppContext session format
        const session = {
          id: response.data.id.toString(),
          userId: response.data.user_id.toString(),
          code: '', // Will be loaded from workspace files
          language: 'python' as const,
          createdAt: new Date(response.data.created_at),
          updatedAt: new Date(response.data.updated_at),
          isActive: true
        };
        
        // Set session in context
        setSession(session);
        
        // Try to load workspace files and start container
        Promise.all([
          apiService.loadSessionWorkspace(sessionId),
          apiService.startContainerSession(sessionId)
        ]).then(async () => {
          console.log('Workspace initialized successfully');
          
          // Load the workspace files to get script.py content
          try {
            const workspaceResponse = await apiService.getSessionWithWorkspace(sessionId);
            const scriptFile = workspaceResponse.workspace_items.find(item => item.name === 'script.py' && item.type === 'file');
            
            if (scriptFile?.content) {
              // Update the code in the context and session
              updateCode(scriptFile.content);
              console.log('Loaded script.py content into editor');
            }
          } catch (workspaceLoadError) {
            console.warn('Could not load workspace files:', workspaceLoadError);
          }
        }).catch(workspaceError => {
          console.warn('Could not initialize workspace:', workspaceError);
          // Continue anyway - workspace might not exist yet or container might be starting
        });
        
      } catch (error) {
        console.error('Failed to load session:', error);
        setSessionLoadError(error instanceof Error ? error.message : 'Failed to load workspace');
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [params.id, isAuthenticated, authLoading]); // Remove function dependencies to prevent infinite loops

  // Loading state
  if (authLoading || state.isLoading) {
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