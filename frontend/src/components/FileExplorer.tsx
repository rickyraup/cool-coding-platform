'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import type { FileItem } from '../context/AppContext';
import { useApp } from '../context/AppContext';
import { useWorkspaceApi } from '../hooks/useWorkspaceApi';
import { useWebSocket } from '../hooks/useWebSocket';
import { deleteFile } from '../services/workspaceApi';

export function FileExplorer(): JSX.Element {
  const { state, setCurrentFile, setFiles } = useApp();
  const { manualSave, loadFileContent, refreshFiles, sessionUuid } = useWorkspaceApi();
  const { sendTerminalCommand } = useWebSocket();
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

  // Delete file handler
  const handleDeleteFile = useCallback(async (filename: string, filePath: string) => {
    if (!sessionUuid) {
      console.error('No session UUID available for delete');
      return;
    }

    try {
      console.log('🗑️ Deleting file:', filename);
      await deleteFile(sessionUuid, filename);

      // Clear current file if it was the deleted file
      if (state.currentFile === filePath) {
        setCurrentFile(null);
      }

      // Refresh file list to reflect changes
      await refreshFiles();
      console.log('✅ File deleted successfully:', filename);
    } catch (error) {
      console.error('Failed to delete file:', error);
      // You could show a toast notification here
    }
  }, [sessionUuid, state.currentFile, setCurrentFile, refreshFiles]);

  const loadFiles = useCallback(async (path: string = '', showErrors: boolean = false) => {
    if (!sessionUuid) {
      if (showErrors) {
        console.error('No session UUID available');
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
      console.log('🔄 [FileExplorer] Loading files via new API');
      const success = await refreshFiles();
      if (!success && showErrors) {
        console.error('Failed to refresh files');
      }
    } catch (error) {
      if (showErrors) {
        console.error('Error loading files:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [sessionUuid, refreshFiles]);

  const loadDirectoryContents = useCallback(async (path: string) => {
    // For now, since we only support flat file structure, just refresh the main files
    try {
      await refreshFiles();
    } catch (error) {
      console.error('Error loading directory contents:', error);
    }
  }, [refreshFiles]);

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
      // Always fetch fresh content from backend when switching files
      console.log('🔄 [FileExplorer] Switching to file and fetching fresh content:', file.path);
      setCurrentFile(file.path);

      // Load file content using new API
      loadFileContent(file.name);
    }
  }, [loadDirectoryContents, setCurrentFile, loadFileContent]);

   
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

  const handleCreateItem = useCallback(async () => {
    if (!newItemName.trim()) return;

    try {
      if (showCreateDialog === 'file') {
        // Create file
        let fileName = !newItemName.includes('.') ? `${newItemName}.py` : newItemName;

        // If we're in a subdirectory, prepend the current directory path
        if (currentDirectory) {
          fileName = `${currentDirectory}/${fileName}`;
        }

        console.log('Creating new file:', fileName);

        // Create file with empty content using the manualSave function
        const success = await manualSave('', fileName);

        if (success) {
          console.log('File created successfully:', fileName);
          // Refresh the file list to show the new file
          await refreshFiles();

          // Automatically select the new file
          setCurrentFile(fileName);

          console.log('File explorer refreshed after creating:', fileName);
        } else {
          console.error('Failed to create file:', fileName);
        }
      } else {
        // Directory creation not implemented yet
        console.log('Directory creation not implemented yet');
      }
    } catch (error) {
      console.error('Error creating file:', error);
    } finally {
      setShowCreateDialog(null);
      setNewItemName('');
    }
  }, [newItemName, showCreateDialog, currentDirectory, manualSave, refreshFiles, setCurrentFile]);

   
  const _handleDeleteItem = useCallback((file: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${file.name}"?`)) {
      // Delete functionality not implemented in new API yet
      console.log('Delete file functionality not implemented in new API yet');
      
      // If deleting current file, clear it
      if (state.currentFile === file.path) {
        setCurrentFile(null);
      }
    }
  }, [state.currentFile, setCurrentFile]);

   
  const _handleExecuteFile = useCallback((file: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (file.type === 'file' && file.name.endsWith('.py')) {
      // Execute Python file via terminal using full path
      const command = `python "${file.path}"`;
      console.log('🚀 Executing file via handleExecuteFile:', command);
      // Terminal command functionality will be implemented later
      console.log('Terminal command functionality not implemented yet:', command);
    }
  }, []);


  // Reset file loading flag when session changes
  useEffect(() => {
    hasLoadedInitialFiles.current = false;
  }, [state.currentSession?.id]);

  // Load real files from backend when session is available
  useEffect(() => {
    if (sessionUuid && state.currentSession && !hasLoadedInitialFiles.current) {
      hasLoadedInitialFiles.current = true;
      console.log('🔄 [FileExplorer] Loading initial files for session:', state.currentSession.id);
      loadFiles('');
    }
  }, [sessionUuid, state.currentSession, loadFiles]);

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
      case 'html':
        return <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.565-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z"/>
        </svg>;
      case 'css':
        return <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm17.09 4.413L5.41 4.41l.213 2.622 10.125.002-.255 2.716h-6.64l.24 2.573h6.182l-.366 3.523-2.91.804-2.956-.81-.188-2.11h-2.61l.29 3.855L12 19.288l5.373-1.53L18.59 4.414z"/>
        </svg>;
      case 'json':
        return <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5.85 3.5a3.5 3.5 0 00-3.5 3.5v1a1.5 1.5 0 01-1.5 1.5.75.75 0 000 1.5 1.5 1.5 0 011.5 1.5v1a3.5 3.5 0 003.5 3.5.75.75 0 000-1.5 2 2 0 01-2-2v-1a3 3 0 00-.879-2.121A3 3 0 004.85 9.5v-1a2 2 0 012-2 .75.75 0 000-1.5zm12.3 0a.75.75 0 000 1.5 2 2 0 012 2v1a3 3 0 00.879 2.121A3 3 0 0019.15 12.5v1a2 2 0 01-2 2 .75.75 0 000 1.5 3.5 3.5 0 003.5-3.5v-1a1.5 1.5 0 011.5-1.5.75.75 0 000-1.5 1.5 1.5 0 01-1.5-1.5v-1a3.5 3.5 0 00-3.5-3.5z"/>
        </svg>;
      case 'md':
      case 'markdown':
        return <svg className="w-4 h-4 text-blue-300" fill="currentColor" viewBox="0 0 24 24">
          <path d="M22.27 19.385H1.73A1.73 1.73 0 010 17.655V6.345a1.73 1.73 0 011.73-1.73h20.54A1.73 1.73 0 0124 6.345v11.31a1.73 1.73 0 01-1.73 1.73zM5.769 15.923v-4.5l2.308 2.885 2.307-2.885v4.5h2.308V8.077h-2.308l-2.307 2.885-2.308-2.885H3.46v7.846h2.309zm13.846-4.5H16.23v4.5h-2.307v-4.5h-3.385V9.23h9.077v2.192z"/>
        </svg>;
      case 'txt':
        return <svg className="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>;
      case 'csv':
        return <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8s0 0 0 0l-6-6zM9.5 7.5H12v1.5H9.5v1.5H12v1.5H9.5V13h3v1.5h-3V16H12v1.5H9.5z"/>
        </svg>;
      case 'xml':
        return <svg className="w-4 h-4 text-orange-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5.85 3.5a3.5 3.5 0 00-3.5 3.5v1a1.5 1.5 0 01-1.5 1.5.75.75 0 000 1.5 1.5 1.5 0 011.5 1.5v1a3.5 3.5 0 003.5 3.5.75.75 0 000-1.5 2 2 0 01-2-2v-1a3 3 0 00-.879-2.121A3 3 0 004.85 9.5v-1a2 2 0 012-2 .75.75 0 000-1.5zm12.3 0a.75.75 0 000 1.5 2 2 0 012 2v1a3 3 0 00.879 2.121A3 3 0 0019.15 12.5v1a2 2 0 01-2 2 .75.75 0 000 1.5 3.5 3.5 0 003.5-3.5v-1a1.5 1.5 0 011.5-1.5.75.75 0 000-1.5 1.5 1.5 0 01-1.5-1.5v-1a3.5 3.5 0 00-3.5-3.5z"/>
        </svg>;
      case 'java':
        return <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8.851 18.56s-.917.534.653.714c1.902.218 2.874.187 4.969-.211 0 0 .552.346 1.321.646-4.699 2.013-10.633-.118-6.943-1.149M8.276 15.933s-1.028.761.542.924c2.032.209 3.636.227 6.413-.308 0 0 .384.389.987.602-5.679 1.661-12.007.13-7.942-1.218"/>
        </svg>;
      case 'c':
      case 'cpp':
      case 'h':
        return <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
          <path d="M22.394 6c-.167-.29-.398-.543-.652-.69L12.926.22c-.509-.294-1.34-.294-1.848 0L2.26 5.31c-.508.293-.923 1.013-.923 1.6v10.18c0 .294.104.62.271.91.167.29.398.543.652.69l8.816 5.09c.508.293 1.339.293 1.848 0l8.816-5.09c.254-.147.485-.4.652-.69.167-.29.27-.616.27-.91V6.91c.003-.294-.1-.62-.268-.91zM12 19.11c-3.92 0-7.109-3.19-7.109-7.11 0-3.92 3.19-7.11 7.109-7.11a7.133 7.133 0 016.156 3.553l-3.076 1.78a3.567 3.567 0 00-3.08-1.78A3.56 3.56 0 008.444 12 3.56 3.56 0 0012 15.555a3.57 3.57 0 003.08-1.778l3.078 1.78A7.135 7.135 0 0112 19.11z"/>
        </svg>;
      case 'sh':
      case 'bash':
        return <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 24 24">
          <path d="M21.038 4.9l-7.577-4.498c-.914-.543-2.009-.543-2.924 0L2.96 4.9C2.046 5.443 1.5 6.398 1.5 7.503v8.995c0 1.104.546 2.059 1.46 2.603l7.577 4.497c.914.543 2.009.543 2.924 0l7.577-4.497c.914-.544 1.46-1.499 1.46-2.603V7.503c0-1.105-.546-2.06-1.46-2.603z"/>
        </svg>;
      case 'yml':
      case 'yaml':
        return <svg className="w-4 h-4 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5.85 3.5a3.5 3.5 0 00-3.5 3.5v1a1.5 1.5 0 01-1.5 1.5.75.75 0 000 1.5 1.5 1.5 0 011.5 1.5v1a3.5 3.5 0 003.5 3.5.75.75 0 000-1.5 2 2 0 01-2-2v-1a3 3 0 00-.879-2.121A3 3 0 004.85 9.5v-1a2 2 0 012-2 .75.75 0 000-1.5zm12.3 0a.75.75 0 000 1.5 2 2 0 012 2v1a3 3 0 00.879 2.121A3 3 0 0019.15 12.5v1a2 2 0 01-2 2 .75.75 0 000 1.5 3.5 3.5 0 003.5-3.5v-1a1.5 1.5 0 011.5-1.5.75.75 0 000-1.5 1.5 1.5 0 01-1.5-1.5v-1a3.5 3.5 0 00-3.5-3.5z"/>
        </svg>;
      case 'sql':
        return <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2l10 6-10 6L2 8l10-6zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>;
      case 'php':
        return <svg className="w-4 h-4 text-purple-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M7.01 10.207h-.944l-.515 2.648h.838c.556 0 .97-.105 1.242-.314.272-.21.455-.559.55-1.049.092-.47.05-.802-.124-.995-.175-.193-.523-.29-1.047-.29zM12 5.688C5.373 5.688 0 8.514 0 12s5.373 6.313 12 6.313S24 15.486 24 12c0-3.486-5.373-6.312-12-6.312z"/>
        </svg>;
      case 'go':
        return <svg className="w-4 h-4 text-cyan-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M1.811 10.231c-.047 0-.058-.023-.035-.059l.246-.315c.023-.035.081-.058.128-.058h4.172c.046 0 .058.035.035.07l-.199.303c-.023.036-.082.07-.117.07zM.047 11.306c-.047 0-.059-.023-.035-.058l.245-.316c.023-.035.082-.058.129-.058h5.516c.047 0 .07.035.058.07l-.093.28c-.012.047-.058.07-.105.07z"/>
        </svg>;
      case 'rust':
      case 'rs':
        return <svg className="w-4 h-4 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.8346 11.7033l-1.0073-.6236a13.7268 13.7268 0 00-.0283-.2936l.8656-.8069a.3483.3483 0 00-.1154-.5702l-1.3647-.5178a.3483.3483 0 00-.4423.1961l-.5178 1.0073a13.7268 13.7268 0 00-.2936.0283l-.8069-.8656a.3483.3483 0 00-.5702.1154l-.5178 1.3647a.3483.3483 0 00.1961.4423z"/>
        </svg>;
      case 'rb':
        return <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.156.083L12 4.8 3.844.083l-.688 15.509L12 24l8.844-8.408L20.156.083zM6.51 17.509l-.344-7.842L12 6.667l5.834 3L17.49 17.509 12 21l-5.49-3.491z"/>
        </svg>;
      case 'swift':
        return <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M7.508 0c-.287 0-.573.098-.798.323L.323 6.71C.098 6.935 0 7.221 0 7.508s.098.573.323.798l6.387 6.387c.225.225.511.323.798.323s.573-.098.798-.323l6.387-6.387c.225-.225.323-.511.323-.798s-.098-.573-.323-.798L8.306.323C8.081.098 7.795 0 7.508 0z"/>
        </svg>;
      case 'kt':
      case 'kts':
        return <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 24H0V0h24L12 12 24 24z"/>
        </svg>;
      case 'dockerfile':
        return <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.186"/>
        </svg>;
      case 'env':
        return <svg className="w-4 h-4 text-green-300" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>;
      default:
        return <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>;
    }
  }, [expandedDirs]);

  // Helper function to get file type badge
  const getFileTypeBadge = useCallback((file: FileItem): string | null => {
    if (file.type === 'directory') return null;

    const ext = file.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py': return 'PY';
      case 'js': return 'JS';
      case 'jsx': return 'JSX';
      case 'ts': return 'TS';
      case 'tsx': return 'TSX';
      case 'html': return 'HTML';
      case 'css': return 'CSS';
      case 'json': return 'JSON';
      case 'md':
      case 'markdown': return 'MD';
      case 'txt': return 'TXT';
      case 'csv': return 'CSV';
      case 'xml': return 'XML';
      case 'java': return 'JAVA';
      case 'c': return 'C';
      case 'cpp': return 'CPP';
      case 'h': return 'H';
      case 'sh':
      case 'bash': return 'SH';
      case 'yml':
      case 'yaml': return 'YAML';
      case 'sql': return 'SQL';
      case 'php': return 'PHP';
      case 'go': return 'GO';
      case 'rust':
      case 'rs': return 'RUST';
      case 'rb': return 'RUBY';
      case 'swift': return 'SWIFT';
      case 'kt':
      case 'kts': return 'KOTLIN';
      case 'dockerfile': return 'DOCKER';
      case 'env': return 'ENV';
      default: return null;
    }
  }, []);

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
              console.log('🔄 [FileExplorer] Clicking file and fetching fresh content:', file.path);
              setCurrentFile(file.path);
              loadFileContent(file.name);
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
          <span className="truncate flex-1 font-medium flex items-center gap-2">
            {file.name}
            {/* File type badge */}
            {getFileTypeBadge(file) && (
              <span className="px-1.5 py-0.5 text-xs font-mono font-semibold bg-gray-600/80 text-gray-200 rounded border border-gray-500/50 flex-shrink-0">
                {getFileTypeBadge(file)}
              </span>
            )}
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
                  handleDeleteFile(file.name, file.path);
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
              disabled={loading || !sessionUuid}
              className={`p-1.5 rounded-md transition-all duration-200 ${
                loading || !sessionUuid
                  ? 'text-gray-600 cursor-not-allowed opacity-50'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-gray-700/60'
              }`}
              title={
                !sessionUuid
                  ? 'Cannot refresh - No session available'
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