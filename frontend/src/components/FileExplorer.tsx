'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import { useApp, FileItem } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function FileExplorer(): JSX.Element {
  const { state, setFiles, setCurrentFile } = useApp();
  const { performFileOperation, sendTerminalCommand } = useWebSocket();
  const [loading, setLoading] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [showCreateDialog, setShowCreateDialog] = useState<'file' | 'folder' | null>(null);
  const [newItemName, setNewItemName] = useState('');
  const [currentDirectory, setCurrentDirectory] = useState('');
  const [allFiles, setAllFiles] = useState<{[key: string]: FileItem[]}>({});
  const hasLoadedInitialFiles = useRef(false);

  const loadFiles = useCallback(async (path: string = '', showErrors: boolean = false) => {
    if (!state.currentSession) return;
    
    setLoading(true);
    try {
      // Use WebSocket file system operation to list files
      const success = performFileOperation('list', path);
      if (!success && showErrors) {
        console.error('Failed to load files');
      }
      // Note: The actual file list will be received via WebSocket message
      // and handled in the WebSocket message handler
    } catch (error) {
      if (showErrors) {
        console.error('Error loading files:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [state.currentSession, performFileOperation]);

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
    if (state.files.length > 0) {
      setAllFiles(prev => ({
        ...prev,
        [currentDirectory]: state.files
      }));
    }
  }, [state.files, currentDirectory]);

  const handleFileClick = useCallback((file: FileItem) => {
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
      performFileOperation('read', file.path);
    }
  }, [loadDirectoryContents, performFileOperation, setCurrentFile]);

  const handleDirectoryDoubleClick = useCallback((file: FileItem) => {
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

  const handleDeleteItem = useCallback((file: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${file.name}"?`)) {
      performFileOperation('delete', file.path);
      
      // If deleting current file, clear it
      if (state.currentFile === file.path) {
        setCurrentFile(null);
      }
    }
  }, [performFileOperation, state.currentFile, setCurrentFile]);

  const handleExecuteFile = useCallback((file: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (file.type === 'file' && file.name.endsWith('.py')) {
      // Execute Python file via terminal
      const command = `python ${file.name}`;
      sendTerminalCommand(command);
    }
  }, [sendTerminalCommand]);


  // Load real files from backend when connected
  useEffect(() => {
    if (state.isConnected && state.currentSession && !hasLoadedInitialFiles.current) {
      hasLoadedInitialFiles.current = true;
      loadFiles('');
    }
  }, [state.isConnected, state.currentSession]);

  const getFileIcon = useCallback((file: FileItem): string => {
    if (file.type === 'directory') {
      return expandedDirs.has(file.path) ? '📂' : '📁';
    }
    
    // File icons based on extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return '🐍';
      case 'js':
      case 'jsx':
        return '📜';
      case 'ts':
      case 'tsx':
        return '📘';
      case 'html':
        return '🌐';
      case 'css':
        return '🎨';
      case 'json':
        return '📋';
      case 'md':
        return '📝';
      case 'txt':
        return '📄';
      default:
        return '📄';
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
          
          <span className="text-base flex-shrink-0">{file.type === 'directory' ? (expandedDirs.has(file.path) ? '📂' : '📁') : '🐍'}</span>
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
                    const command = `python ${file.name}`;
                    sendTerminalCommand(command);
                  }
                }}
                className="p-1 text-green-400 hover:text-green-300 hover:bg-green-400/20 rounded transition-colors"
                title="Run Python file"
              >
                ▶
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
              🗑
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
      <div className="bg-gray-800 px-4 py-3 border-b border-gray-600">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-200">Explorer</h2>
          <div className="flex gap-1">
            <button
              onClick={() => loadFiles(currentDirectory, true)} // Show errors for user-initiated refresh
              disabled={loading}
              className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-50 rounded transition-colors"
              title="Refresh"
            >
              🔄
            </button>
            <button
              onClick={() => setShowCreateDialog('file')}
              className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
              title="New File"
            >
              📄
            </button>
            <button
              onClick={() => setShowCreateDialog('folder')}
              className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
              title="New Folder"
            >
              📁
            </button>
          </div>
        </div>
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <button
            onClick={handleNavigateToRoot}
            className="hover:text-white transition-colors px-1 py-0.5 rounded"
          >
            📁 Root
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
            <div className="animate-spin">🔄</div>
            Loading files...
          </div>
        ) : state.files.length === 0 ? (
          <div className="p-4 text-sm text-gray-400 text-center">
            <div className="text-2xl mb-2">📂</div>
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