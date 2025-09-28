'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import type { FileItem } from '../context/AppContext';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function FileExplorer(): JSX.Element {
  const { state, setCurrentFile } = useApp();
  const { performFileOperation, sendTerminalCommand } = useWebSocket();
  const [loading, setLoading] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [showCreateDialog, setShowCreateDialog] = useState<'file' | 'folder' | null>(null);
  const [newItemName, setNewItemName] = useState('');
  const [currentDirectory, setCurrentDirectory] = useState('');
  const [allFiles, setAllFiles] = useState<{[key: string]: FileItem[]}>({});
  const hasLoadedInitialFiles = useRef(false);
  const fileContentCache = useRef<{[key: string]: string}>({});
  const lastFileReadTime = useRef<{[key: string]: number}>({});
  const lastDirectoryListTime = useRef<{[key: string]: number}>({});

  const loadFiles = useCallback(async (path: string = '', showErrors: boolean = false) => {
    if (!state.currentSession) {
      if (showErrors) {
        console.error('No current session available');
      }
      return;
    }
    
    if (!state.isConnected) {
      if (showErrors) {
        console.error('WebSocket not connected');
      }
      return;
    }
    
    // Debounce directory listing requests (1 second)
    const now = Date.now();
    const lastList = lastDirectoryListTime.current[path] || 0;
    const timeSinceLastList = now - lastList;
    const DEBOUNCE_DELAY = 1000; // 1 second
    
    if (timeSinceLastList < DEBOUNCE_DELAY) {
      console.log('🚫 [FileExplorer] Debouncing directory list request for:', path);
      return;
    }
    
    lastDirectoryListTime.current[path] = now;
    setLoading(true);
    try {
      console.log('🔄 [FileExplorer] Loading files for path:', path);
      // Use WebSocket file system operation to list files
      const success = performFileOperation('list', path);
      if (!success) {
        if (showErrors) {
          console.error('Failed to send file list request - WebSocket not ready');
        }
        // Don't keep loading state if the request failed
        setLoading(false);
      }
      // Note: The actual file list will be received via WebSocket message
      // and handled in the WebSocket message handler. Loading state will be cleared there.
    } catch (error) {
      if (showErrors) {
        console.error('Error loading files:', error);
      }
      setLoading(false);
    }
  }, [state.currentSession, state.isConnected, performFileOperation]);

  const loadDirectoryContents = useCallback(async (path: string) => {
    if (!state.currentSession) return;
    
    try {
      const success = performFileOperation('list', path);
      if (!success) {
        console.error('Failed to load directory contents');
      }
    } catch (error) {
      console.error('Error loading directory contents:', error);
    }
  }, [state.currentSession, performFileOperation]);

  // Update allFiles when state.files changes
  useEffect(() => {
    if (state.files.length >= 0) { // Include empty arrays (0 files is valid)
      setAllFiles(prev => ({
        ...prev,
        [currentDirectory]: state.files
      }));
      // Clear loading state when files are received
      setLoading(false);
    }
  }, [state.files, currentDirectory]);

   
  const _handleFileClick = useCallback((file: FileItem) => {
    if (file.type === 'directory') {
      // Toggle directory expansion
      setExpandedDirs(prev => {
        const newSet = new Set(prev);
        if (newSet.has(file.path)) {
          newSet.delete(file.path);
        } else {
          newSet.add(file.path);
          // Load directory contents for expansion
          loadDirectoryContents(file.path);
        }
        return newSet;
      });
    } else {
      // Load file content into editor and mark as current
      setCurrentFile(file.path);
      
      // Check if we have cached content and it's recent (within 5 seconds)
      const now = Date.now();
      const lastRead = lastFileReadTime.current[file.path] || 0;
      const cacheAge = now - lastRead;
      const CACHE_DURATION = 5000; // 5 seconds
      
      if (fileContentCache.current[file.path] && cacheAge < CACHE_DURATION) {
        console.log('🚀 [FileExplorer] Using cached content for:', file.path);
        // Use cached content without making WebSocket request
        return;
      }
      
      console.log('🔄 [FileExplorer] Reading file content for:', file.path);
      lastFileReadTime.current[file.path] = now;
      performFileOperation('read', file.path);
    }
  }, [loadDirectoryContents, performFileOperation, setCurrentFile]);

   
  const _handleDirectoryDoubleClick = useCallback((file: FileItem) => {
    if (file.type === 'directory') {
      // Navigate into directory on double-click
      setCurrentDirectory(file.path);
      setExpandedDirs(new Set()); // Reset expanded dirs when navigating
      loadFiles(file.path, true); // Show errors for user-initiated actions
    }
  }, [loadFiles]);

  const handleNavigateUp = useCallback(() => {
    if (currentDirectory) {
      // Navigate to parent directory
      const parentPath = currentDirectory.split('/').slice(0, -1).join('/');
      setCurrentDirectory(parentPath);
      loadFiles(parentPath, true); // Show errors for user-initiated actions
    }
  }, [currentDirectory, loadFiles]);

  const handleNavigateToRoot = useCallback(() => {
    setCurrentDirectory('');
    loadFiles('', true); // Show errors for user-initiated actions
  }, [loadFiles]);

  const handleCreateItem = useCallback(() => {
    if (!newItemName.trim()) return;

    const action = showCreateDialog === 'file' ? 'create_file' : 'create_directory';
    let fileName = showCreateDialog === 'file' && !newItemName.includes('.') ? 
      `${newItemName}.py` : newItemName;

    // If we're in a subdirectory, prepend the current directory path
    if (currentDirectory) {
      fileName = `${currentDirectory}/${fileName}`;
    }

    performFileOperation(action, fileName, showCreateDialog === 'file' ? '# New file\n' : '');
    
    setShowCreateDialog(null);
    setNewItemName('');
  }, [newItemName, showCreateDialog, currentDirectory, performFileOperation]);

   
  const _handleDeleteItem = useCallback((file: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${file.name}"?`)) {
      performFileOperation('delete', file.path);
      
      // If deleting current file, clear it
      if (state.currentFile === file.path) {
        setCurrentFile(null);
      }
    }
  }, [performFileOperation, state.currentFile, setCurrentFile]);

   
  const _handleExecuteFile = useCallback((file: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (file.type === 'file' && file.name.endsWith('.py')) {
      // Execute Python file via terminal using full path
      const command = `python "${file.path}"`;
      console.log('🚀 Executing file via handleExecuteFile:', command);
      sendTerminalCommand(command);
    }
  }, [sendTerminalCommand]);


  // Reset file loading flag when session changes
  useEffect(() => {
    hasLoadedInitialFiles.current = false;
  }, [state.currentSession?.id]);

  // Load real files from backend when connected
  useEffect(() => {
    if (state.isConnected && state.currentSession && !hasLoadedInitialFiles.current) {
      hasLoadedInitialFiles.current = true;
      console.log('🔄 [FileExplorer] Loading initial files for session:', state.currentSession.id);
      loadFiles('');
    }
  }, [state.isConnected, state.currentSession, loadFiles]);

  const getFileIconComponent = useCallback((file: FileItem): JSX.Element => {
    if (file.type === 'directory') {
      const isExpanded = expandedDirs.has(file.path);
      return (
        <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
          {isExpanded ? (
            <path d="M19 7h-3V6a2 2 0 00-2-2H4a2 2 0 00-2 2v11a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2z" />
          ) : (
            <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2z" />
          )}
        </svg>
      );
    }
    
    // File icons based on extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14.25 2.1l-.1-.1-.1-.1c-.1-.1-.2-.1-.3-.1H7.85C7.38 1.9 7 2.28 7 2.75v18.5c0 .47.38.85.85.85h8.3c.47 0 .85-.38.85-.85V6.75c0-.12-.05-.23-.15-.33l-2.6-2.6z"/>
        </svg>;
      case 'js':
      case 'jsx':
        return <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 3h18v18H3V3zm16.525 13.707c-.131-.821-.666-1.511-2.252-2.155-.552-.259-1.165-.438-1.349-.854-.068-.248-.078-.382-.034-.529.113-.484.687-.629 1.137-.495.293.09.563.315.732.676.775-.507.775-.507 1.316-.844-.203-.314-.304-.451-.439-.586-.473-.528-1.103-.798-2.126-.77l-.528.067c-.507.124-.991.395-1.283.754-.855.968-.608 2.655.427 3.354 1.023.765 2.521.933 2.712 1.653.18.878-.652 1.159-1.475 1.058-.607-.136-.945-.439-1.316-.1l1.386-.9c.5.706 1.232.706 1.232.706s1.07.123 1.07-.706v-.051z"/>
        </svg>;
      case 'ts':
      case 'tsx':
        return <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.373 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375z"/>
        </svg>;
      default:
        return <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>;
    }
  }, [expandedDirs]);

  // Build hierarchical tree structure for rendering
  const buildFileTree = useCallback((basePath: string = currentDirectory, depth: number = 0, visited: Set<string> = new Set()) => {
    // Prevent infinite recursion
    if (visited.has(basePath) || depth > 10) {
      console.warn('Preventing infinite recursion in buildFileTree:', basePath, depth);
      return [];
    }
    
    visited.add(basePath);
    const files = allFiles[basePath] || [];
    const items: React.ReactElement[] = [];
    
    files.forEach((file, index) => {
      // File/directory item
      items.push(
        <div
          key={`${file.path}-${index}`}
          onClick={() => {
            if (file.type === 'directory') {
              setExpandedDirs(prev => {
                const newSet = new Set(prev);
                if (newSet.has(file.path)) {
                  newSet.delete(file.path);
                } else {
                  newSet.add(file.path);
                  loadDirectoryContents(file.path);
                }
                return newSet;
              });
            } else {
              setCurrentFile(file.path);
              performFileOperation('read', file.path);
            }
          }}
          onDoubleClick={() => {
            if (file.type === 'directory') {
              setCurrentDirectory(file.path);
              setExpandedDirs(new Set());
              loadFiles(file.path, true); // Show errors for user-initiated actions
            }
          }}
          className={`flex items-center gap-3 px-3 py-2 cursor-pointer group text-sm transition-all duration-150 ${
            state.currentFile === file.path 
              ? 'bg-blue-600/90 text-white border-r-2 border-blue-400' 
              : 'hover:bg-gray-700/70 text-gray-200 hover:text-white'
          }`}
          style={{ paddingLeft: `${12 + depth * 20}px` }}
        >
          {file.type === 'directory' && (
            <span 
              className={`text-xs transition-transform duration-200 flex-shrink-0 ${
                expandedDirs.has(file.path) ? 'rotate-90' : ''
              }`}
              onClick={(e) => {
                e.stopPropagation();
                setExpandedDirs(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(file.path)) {
                    newSet.delete(file.path);
                  } else {
                    newSet.add(file.path);
                    loadDirectoryContents(file.path);
                  }
                  return newSet;
                });
              }}
            >
              ▶
            </span>
          )}
          
          <span className="flex-shrink-0">{getFileIconComponent(file)}</span>
          <span className="truncate flex-1 font-medium">
            {file.name}
          </span>
          
          {/* Action buttons */}
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {file.type === 'file' && file.name.endsWith('.py') && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (file.type === 'file' && file.name.endsWith('.py')) {
                    // Use the full path for execution
                    const command = `python "${file.path}"`;
                    console.log('🚀 Executing file:', command);
                    sendTerminalCommand(command);
                  }
                }}
                className="p-1 text-green-400 hover:text-green-300 hover:bg-green-400/20 rounded transition-colors"
                title="Run Python file"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </button>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`Are you sure you want to delete "${file.name}"?`)) {
                  performFileOperation('delete', file.path);
                  if (state.currentFile === file.path) {
                    setCurrentFile(null);
                  }
                }
              }}
              className="p-1 text-red-400 hover:text-red-300 hover:bg-red-400/20 rounded transition-colors"
              title="Delete"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      );
      
      // If directory is expanded, recursively render its contents
      if (file.type === 'directory' && expandedDirs.has(file.path) && allFiles[file.path] && !visited.has(file.path)) {
        const subItems = buildFileTree(file.path, depth + 1, new Set(visited));
        items.push(...subItems);
      }
    });
    
    return items;
  }, [allFiles, currentDirectory, expandedDirs, state.currentFile]);


  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <h2 className="text-sm font-medium text-gray-100">Explorer</h2>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => {
                console.log('🔄 Refresh button clicked');
                hasLoadedInitialFiles.current = false; // Reset the flag to force reload
                loadFiles(currentDirectory, true); // Show errors for user-initiated refresh
              }}
              disabled={loading || !state.isConnected}
              className={`p-1.5 rounded-md transition-all duration-200 ${
                loading || !state.isConnected
                  ? 'text-gray-600 cursor-not-allowed opacity-50'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-gray-700/60'
              }`}
              title={
                !state.isConnected 
                  ? 'Cannot refresh - WebSocket disconnected' 
                  : loading 
                    ? 'Loading...' 
                    : 'Refresh files'
              }
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              onClick={() => setShowCreateDialog('file')}
              className="p-1.5 text-gray-400 hover:text-gray-100 hover:bg-gray-700/60 rounded-md transition-all duration-200"
              title="New File"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={() => setShowCreateDialog('folder')}
              className="p-1.5 text-gray-400 hover:text-gray-100 hover:bg-gray-700/60 rounded-md transition-all duration-200"
              title="New Folder"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <button
            onClick={handleNavigateToRoot}
            className="hover:text-white transition-colors px-1 py-0.5 rounded"
          >
            <svg className="w-3 h-3 inline mr-1" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            Root
          </button>
          {currentDirectory && (
            <>
              {currentDirectory.split('/').map((folder, index, arr) => {
                const isLast = index === arr.length - 1;
                const pathSoFar = arr.slice(0, index + 1).join('/');
                
                return (
                  <div key={index} className="flex items-center gap-1">
                    <span className="text-gray-600">/</span>
                    {isLast ? (
                      <span className="text-blue-400 font-medium">{folder}</span>
                    ) : (
                      <button
                        onClick={() => {
                          setCurrentDirectory(pathSoFar);
                          loadFiles(pathSoFar, true); // Show errors for user-initiated navigation
                        }}
                        className="hover:text-white transition-colors px-1 py-0.5 rounded"
                      >
                        {folder}
                      </button>
                    )}
                  </div>
                );
              })}
              <button
                onClick={handleNavigateUp}
                className="ml-2 p-1 text-gray-500 hover:text-white transition-colors rounded"
                title="Go up"
              >
                ↑
              </button>
            </>
          )}
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-sm text-gray-400 flex items-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Loading files...
          </div>
        ) : state.files.length === 0 ? (
          <div className="p-4 text-sm text-gray-400 text-center">
            <svg className="w-8 h-8 mx-auto mb-2 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            No files found
          </div>
        ) : (
          <div className="py-1">
            {buildFileTree()}
          </div>
        )}
      </div>

      {/* Status */}
      <div className="bg-gray-800 px-3 py-2 border-t border-gray-600">
        <div className="text-xs text-gray-400 font-mono">
          {state.files.length} {state.files.length === 1 ? 'item' : 'items'}
        </div>
      </div>

      {/* Create Item Dialog */}
      {showCreateDialog && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-80 border border-gray-600">
            <h3 className="text-lg font-semibold text-white mb-2">
              Create New {showCreateDialog === 'file' ? 'File' : 'Folder'}
            </h3>
            
            {currentDirectory && (
              <p className="text-sm text-gray-400 mb-4">
                in: /{currentDirectory}
              </p>
            )}
            
            <input
              type="text"
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateItem();
                if (e.key === 'Escape') {
                  setShowCreateDialog(null);
                  setNewItemName('');
                }
              }}
              placeholder={showCreateDialog === 'file' ? 'filename.py' : 'folder-name'}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              autoFocus
            />
            
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleCreateItem}
                disabled={!newItemName.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowCreateDialog(null);
                  setNewItemName('');
                }}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}