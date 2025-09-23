'use client';

import { useCallback, useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { useApp } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';

export function CodeEditor(): JSX.Element {
  const { state, updateCode } = useApp();
  const { saveCurrentFile } = useWebSocket();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleEditorDidMount = useCallback((editorInstance: editor.IStandaloneCodeEditor): void => {
    editorRef.current = editorInstance;
    
    // Add keyboard shortcuts
    editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      // Trigger code execution (we'll implement this later)
      console.log('Execute code shortcut triggered');
    });
    
    editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      // Save code (prevent browser default)
      console.log('Save code shortcut triggered');
    });
  }, []);

  const handleEditorChange = useCallback((value: string | undefined): void => {
    const newCode = value ?? '';
    updateCode(newCode);
    
    // Auto-save with debounce (save 2 seconds after user stops typing)
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    
    autoSaveTimeoutRef.current = setTimeout(() => {
      if (newCode.trim() && state.currentSession) {
        saveCurrentFile(newCode);
      }
    }, 2000);
  }, [updateCode, saveCurrentFile, state.currentSession]);

  // Cleanup auto-save timeout on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);

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
            readOnly: false,
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
      
      <div className="bg-gray-800 border-t border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          {state.currentFile && (
            <>
              <span className="text-blue-400 font-medium">📄 {state.currentFile}</span>
              <span>•</span>
            </>
          )}
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
        
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          {state.error && (
            <span className="text-red-400">Error: {state.error}</span>
          )}
          <span>{state.code.length} characters</span>
          <span>Monaco Editor</span>
        </div>
      </div>
    </div>
  );
}