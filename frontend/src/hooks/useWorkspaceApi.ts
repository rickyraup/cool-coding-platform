/**
 * Clean hook for workspace file operations using the new API
 */

import { useCallback } from 'react';
import { saveFileContent, getFileContent, getWorkspaceFiles } from '../services/workspaceApi';
import { useApp } from '../contexts/AppContext';
import { useParams } from 'next/navigation';

export function useWorkspaceApi() {
  const { state, markSaved, updateCode, setFiles, setCurrentFile, setFileContent } = useApp();
  const params = useParams();
  // Support both workspace pages (/workspace/[id]) and review pages (/review/[sessionId])
  const sessionUuid = (params?.['id'] || params?.['sessionId']) as string;

  // Save current file using the new API
  const manualSave = useCallback(async (content?: string, filename?: string): Promise<boolean> => {
    try {
      if (!sessionUuid) {
        console.error('No session UUID available for save', { params });
        return false;
      }

      const codeToSave = content || state.code;
      const fileToSave = filename || state.currentFile;

      if (!fileToSave) {
        console.error('No file selected for save');
        return false;
      }


      // Save using new API
      const result = await saveFileContent(sessionUuid, fileToSave, codeToSave);


      // Mark as saved in context
      markSaved(codeToSave);

      return true;
    } catch (error) {
      console.error('Failed to save file:', error);
      return false;
    }
  }, [sessionUuid, state.code, state.currentFile, markSaved]);

  // Load file content using the new API
  const loadFileContent = useCallback(async (filename: string): Promise<boolean> => {
    try {
      if (!sessionUuid) {
        console.error('No session UUID available for load', { params, filename });
        return false;
      }


      // Load using new API
      const fileContent = await getFileContent(sessionUuid, filename);


      // Update context - use setFileContent to mark as saved
      setCurrentFile(fileContent.path);
      setFileContent(fileContent.path, fileContent.content);

      return true;
    } catch (error) {
      console.error('Failed to load file content:', error);
      return false;
    }
  }, [sessionUuid, setCurrentFile, setFileContent]);

  // Refresh file list
  const refreshFiles = useCallback(async (): Promise<boolean> => {
    try {
      if (!sessionUuid) {
        console.error('No session UUID available for refresh', { params });
        return false;
      }


      // Get files using new API
      const files = await getWorkspaceFiles(sessionUuid);


      // Update context
      setFiles(files);

      return true;
    } catch (error) {
      console.error('Failed to refresh files:', error);
      return false;
    }
  }, [sessionUuid, setFiles]);

  return {
    manualSave,
    loadFileContent,
    refreshFiles,
    sessionUuid
  };
}