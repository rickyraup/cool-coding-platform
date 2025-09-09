'use client';

import { useCallback, useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { useApp } from '../context/AppContext';

export function CodeEditor(): JSX.Element {
  const { state, updateCode } = useApp();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

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
    updateCode(value ?? '');
  }, [updateCode]);

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
          provideCompletionItems: (model, position) => {
            const suggestions: monaco.languages.CompletionItem[] = [
              {
                label: 'print',
                kind: monaco.languages.CompletionItemKind.Function,
                insertText: 'print(${1:})',
                insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                documentation: 'Print function'
              },
              {
                label: 'import pandas as pd',
                kind: monaco.languages.CompletionItemKind.Module,
                insertText: 'import pandas as pd',
                documentation: 'Import pandas library'
              },
              {
                label: 'import numpy as np',
                kind: monaco.languages.CompletionItemKind.Module,
                insertText: 'import numpy as np',
                documentation: 'Import numpy library'
              },
              {
                label: 'import matplotlib.pyplot as plt',
                kind: monaco.languages.CompletionItemKind.Module,
                insertText: 'import matplotlib.pyplot as plt',
                documentation: 'Import matplotlib pyplot'
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
      <div className="flex-1">
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
              enabled: true,
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