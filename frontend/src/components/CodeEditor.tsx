'use client';

import { useCallback, useRef, useEffect, JSX } from 'react';
import Editor from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import type * as Monaco from 'monaco-editor';
import { useApp } from '../contexts/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

interface CodeEditorProps {
  readOnly?: boolean;
}

export function CodeEditor({ readOnly = false }: CodeEditorProps): JSX.Element {
  const { state, updateCode } = useApp();
  const { manualSave } = useWebSocket();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const currentFileRef = useRef<string | null>(null);
  const lastStateCodeRef = useRef<string>('');

  // Keep currentFile in sync with a ref to avoid stale closures
  useEffect(() => {
    currentFileRef.current = state.currentFile;
  }, [state.currentFile]);

  // Track the last code from state to detect programmatic vs user changes
  useEffect(() => {
    lastStateCodeRef.current = state.code;
  }, [state.code]);

  // Create a stable save handler using refs
  const handleSave = useCallback(() => {
    if (currentFileRef.current && editorRef.current) {
      const currentCode = editorRef.current.getValue();
      const currentFile = currentFileRef.current;
      // Update the state immediately before saving
      updateCode(currentCode);
      // Pass the filename explicitly to ensure we save to the correct file
      manualSave(currentCode, currentFile);
    }
  }, [manualSave, updateCode]);

  const handleEditorDidMount = useCallback((editorInstance: editor.IStandaloneCodeEditor, monacoInstance: typeof Monaco): void => {
    editorRef.current = editorInstance;

    // Add keyboard shortcuts
    editorInstance.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.Enter, () => {
      // Code execution via keyboard shortcut not currently supported
    });

    editorInstance.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.KeyS, () => {
      // Save code manually with Ctrl+S/Cmd+S
      handleSave();
    });
  }, [handleSave]);

  // Prevent default browser save behavior
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  const handleEditorChange = useCallback((value: string | undefined): void => {
    if (readOnly) return; // Prevent changes in read-only mode

    const newCode = value ?? '';

    // Don't update state if the value matches what we just set from state
    // This prevents false "unsaved changes" when loading a file
    if (newCode === lastStateCodeRef.current) {
      return;
    }

    updateCode(newCode);
  }, [updateCode, readOnly]);


  useEffect(() => {
    // Configure Monaco editor options
    if (typeof window !== 'undefined') {
      import('monaco-editor').then((monaco) => {
        // Configure Python language features
        monaco.languages.typescript.typescriptDefaults.setEagerModelSync(true);
        
        // Set theme
        monaco.editor.setTheme('vs-dark');
        
        // Configure Python intellisense
        monaco.languages.registerCompletionItemProvider('python', {
          provideCompletionItems: (_model, position) => {
            const range = {
              startLineNumber: position.lineNumber,
              endLineNumber: position.lineNumber,
              startColumn: position.column,
              endColumn: position.column
            };
            const suggestions: import('monaco-editor').languages.CompletionItem[] = [
              {
                label: 'print',
                kind: monaco.languages.CompletionItemKind.Function,
                insertText: 'print(${1:})',
                insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                documentation: 'Print function',
                range
              },
              {
                label: 'import pandas as pd',
                kind: monaco.languages.CompletionItemKind.Module,
                insertText: 'import pandas as pd',
                documentation: 'Import pandas library',
                range
              },
              {
                label: 'import numpy as np',
                kind: monaco.languages.CompletionItemKind.Module,
                insertText: 'import numpy as np',
                documentation: 'Import numpy library',
                range
              },
              {
                label: 'import matplotlib.pyplot as plt',
                kind: monaco.languages.CompletionItemKind.Module,
                insertText: 'import matplotlib.pyplot as plt',
                documentation: 'Import matplotlib pyplot',
                range
              }
            ];
            return { suggestions };
          }
        });
      }).catch((error) => {
        console.error('Failed to configure Monaco editor:', error);
      });
    }
  }, []);

  const getLineCount = (): number => {
    return state.code.split('\n').length;
  };

  const getColumnCount = (): number => {
    if (!editorRef.current) return 1;
    const position = editorRef.current.getPosition();
    return position?.column ?? 1;
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 relative">
        {!state.currentFile && (
          <div className="absolute inset-0 bg-gray-900/95 z-10 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">📁</div>
              <div className="text-xl text-white mb-2">No file selected</div>
              <div className="text-gray-400">Click a file in the explorer to start editing</div>
            </div>
          </div>
        )}
        <Editor
          height="100%"
          defaultLanguage="python"
          value={state.code}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            fontSize: 14,
            fontFamily: 'ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: 'all',
            selectOnLineNumbers: true,
            roundedSelection: false,
            readOnly: readOnly,
            cursorStyle: 'line',
            automaticLayout: true,
            wordWrap: 'on',
            wrappingIndent: 'indent',
            tabSize: 4,
            insertSpaces: true,
            folding: true,
            foldingHighlight: true,
            foldingImportsByDefault: false,
            unfoldOnClickAfterEndOfLine: false,
            bracketPairColorization: {
              enabled: true,
            },
            guides: {
              indentation: true,
              highlightActiveIndentation: true,
            },
            suggest: {
              showWords: true,
              showSnippets: true,
            },
            quickSuggestions: {
              other: true,
              comments: true,
              strings: true,
            },
            parameterHints: {
              enabled: true,
            },
            hover: {
              enabled: true,
            },
          }}
        />
      </div>
      
      {/* Editor Toolbar */}
      <div className="bg-gray-800 border-t border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          {state.currentFile && (
            <>
              <span className="text-blue-400 font-medium flex items-center">
                📄 {state.currentFile}
                {state.hasUnsavedChanges && (
                  <span className="ml-1 w-2 h-2 bg-white rounded-full" title="Unsaved changes"></span>
                )}
              </span>
              <span>•</span>
            </>
          )}
          
          <span className="text-gray-400 text-xs">Press Cmd+S to save</span>
          <span>•</span>
          <span>Python</span>
          <span>•</span>
          <span>UTF-8</span>
          <span>•</span>
          <span>Line {getLineCount()}, Col {getColumnCount()}</span>
          {state.currentSession && (
            <>
              <span>•</span>
              <span>Session: {state.currentSession.id.substring(0, 8)}</span>
            </>
          )}
        </div>
        
        <div className="flex items-center space-x-4 text-sm">
          {state.error && (
            <span className="text-red-400">Error: {state.error}</span>
          )}
          <span className="text-gray-400">{state.code.length} chars</span>
          <span className="text-gray-400">Monaco Editor</span>
        </div>
      </div>
    </div>
  );
}