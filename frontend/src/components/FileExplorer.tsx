'use client';

import { useCallback, useEffect, useState } from 'react';
import { useApp, FileItem } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function FileExplorer(): JSX.Element {
  const { state, setFiles, setCurrentFile } = useApp();
  const { performFileOperation } = useWebSocket();
  const [loading, setLoading] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());


  const loadFiles = useCallback(async (path: string = '') => {
    if (!state.currentSession) return;
    
    setLoading(true);
    try {
      // Use WebSocket file system operation to list files
      const success = performFileOperation('list', path);
      if (!success) {
        console.error('Failed to load files');
      }
      // Note: The actual file list will be received via WebSocket message
      // and handled in the WebSocket message handler
    } catch (error) {
      console.error('Error loading files:', error);
    } finally {
      setLoading(false);
    }
  }, [state.currentSession, performFileOperation]);

  const handleFileClick = useCallback((file: FileItem) => {
    if (file.type === 'directory') {
      // Toggle directory expansion
      setExpandedDirs(prev => {
        const newSet = new Set(prev);
        if (newSet.has(file.path)) {
          newSet.delete(file.path);
        } else {
          newSet.add(file.path);
          // Load directory contents
          loadFiles(file.path);
        }
        return newSet;
      });
    } else {
      // Load file content into editor and mark as current
      setCurrentFile(file.path);
      performFileOperation('read', file.path);
    }
  }, [loadFiles, performFileOperation, setCurrentFile]);

  const getFileIcon = (file: FileItem): string => {
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
  };

  // Load real files from backend when connected
  useEffect(() => {
    if (state.isConnected && state.currentSession) {
      loadFiles('');
    }
  }, [state.isConnected, state.currentSession, loadFiles]);

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-300">Files</h2>
        <div className="flex gap-2">
          <button
            onClick={() => loadFiles('')}
            disabled={loading}
            className="text-xs text-gray-400 hover:text-white disabled:opacity-50"
            title="Refresh"
          >
            🔄
          </button>
          <button
            className="text-xs text-gray-400 hover:text-white"
            title="New File"
          >
            📄+
          </button>
          <button
            className="text-xs text-gray-400 hover:text-white"
            title="New Folder"
          >
            📁+
          </button>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-sm text-gray-400">Loading files...</div>
        ) : state.files.length === 0 ? (
          <div className="p-4 text-sm text-gray-400">No files found</div>
        ) : (
          <div className="py-2">
            {state.files.map((file, index) => (
              <div
                key={`${file.path}-${index}`}
                onClick={() => handleFileClick(file)}
                className={`flex items-center gap-2 px-4 py-1.5 cursor-pointer group text-sm ${
                  state.currentFile === file.path 
                    ? 'bg-blue-600 text-white' 
                    : 'hover:bg-gray-700 text-gray-200'
                }`}
              >
                <span className="text-base">{getFileIcon(file)}</span>
                <span className={`truncate ${
                  state.currentFile === file.path 
                    ? 'text-white' 
                    : 'group-hover:text-white'
                }`}>
                  {file.name}
                </span>
                {file.type === 'directory' && (
                  <span className="text-gray-500 ml-auto">
                    {expandedDirs.has(file.path) ? '▼' : '▶'}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Status */}
      <div className="bg-gray-800 px-4 py-2 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          Session: {state.currentSession?.id || 'None'}
        </div>
      </div>
    </div>
  );
}