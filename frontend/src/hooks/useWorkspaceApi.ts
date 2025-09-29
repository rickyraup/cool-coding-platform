/**
 * Clean hook for workspace file operations using the new API
 */

import { useCallback } from 'react';
import { saveFileContent, getFileContent, getWorkspaceFiles } from '../services/workspaceApi';
import { useApp } from '../context/AppContext';
import { useParams } from 'next/navigation';

export function useWorkspaceApi() {
  const { state, markSaved, updateCode, setFiles, setCurrentFile } = useApp();
  const params = useParams();
  // Support both workspace pages (/workspace/[id]) and review pages (/review/[sessionId])
  const sessionUuid = (params?.id || params?.sessionId) as string;

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

      console.log('Saving file via API:', fileToSave, 'Content length:', codeToSave.length);

      // Save using new API
      const result = await saveFileContent(sessionUuid, fileToSave, codeToSave);

      console.log('File saved successfully:', result);

      // Mark as saved in context
      markSaved(codeToSave);

      return true;
    } catch (error) {
      console.error('Failed to save file:', error);
      return false;
    }
  }, [sessionUuid, markSaved]);

  // Load file content using the new API
  const loadFileContent = useCallback(async (filename: string): Promise<boolean> => {
    try {
      if (!sessionUuid) {
        console.error('No session UUID available for load', { params, filename });
        return false;
      }

      console.log('Loading file content via API:', filename);

      // Load using new API
      const fileContent = await getFileContent(sessionUuid, filename);

      console.log('File content loaded:', fileContent.content.length, 'characters');

      // Update context
      setCurrentFile(fileContent.path);
      updateCode(fileContent.content);

      return true;
    } catch (error) {
      console.error('Failed to load file content:', error);
      return false;
    }
  }, [sessionUuid, setCurrentFile, updateCode]);

  // Refresh file list
  const refreshFiles = useCallback(async (): Promise<boolean> => {
    try {
      if (!sessionUuid) {
        console.error('No session UUID available for refresh', { params });
        return false;
      }

      console.log('Refreshing file list via API');

      // Get files using new API
      const files = await getWorkspaceFiles(sessionUuid);

      console.log('Files refreshed:', files);

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