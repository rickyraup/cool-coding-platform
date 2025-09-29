/**
 * Clean API service for workspace file management
 * Handles per-workspace (UUID session) file operations
 */

const API_BASE_URL = 'http://localhost:8001';

export interface FileItem {
  name: string;
  type: 'file' | 'directory';
  path: string;
}

export interface FileContent {
  name: string;
  path: string;
  content: string;
}

export interface SaveFileResponse {
  message: string;
  file: {
    name: string;
    path: string;
    content: string;
  };
}

/**
 * Get all files in a workspace
 */
export async function getWorkspaceFiles(sessionUuid: string): Promise<FileItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/workspace/${sessionUuid}/files`);

  if (!response.ok) {
    throw new Error(`Failed to fetch workspace files: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get content of a specific file
 */
export async function getFileContent(sessionUuid: string, filename: string): Promise<FileContent> {
  const response = await fetch(`${API_BASE_URL}/api/workspace/${sessionUuid}/file/${encodeURIComponent(filename)}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch file content: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Save content to a specific file
 */
export async function saveFileContent(
  sessionUuid: string,
  filename: string,
  content: string
): Promise<SaveFileResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/workspace/${sessionUuid}/file/${encodeURIComponent(filename)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to save file: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a specific file
 */
export async function deleteFile(sessionUuid: string, filename: string): Promise<{ message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/workspace/${sessionUuid}/file/${encodeURIComponent(filename)}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete file: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Ensure workspace has default files (creates main.py if no files exist)
 */
export async function ensureDefaultFiles(sessionUuid: string): Promise<{
  message: string;
  files_created: string[];
  file?: FileContent;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/workspace/${sessionUuid}/ensure-default`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to ensure default files: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get workspace initialization status
 */
export async function getWorkspaceStatus(sessionUuid: string): Promise<{
  status: 'not_found' | 'empty' | 'ready' | 'initializing' | 'error';
  message: string;
  initialized: boolean;
  filesystem_synced?: boolean;
  file_count?: number;
}> {
  const response = await fetch(`${API_BASE_URL}/api/workspace/${sessionUuid}/status`);

  if (!response.ok) {
    throw new Error(`Failed to fetch workspace status: ${response.statusText}`);
  }

  return response.json();
}