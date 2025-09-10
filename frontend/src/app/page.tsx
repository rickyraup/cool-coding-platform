'use client';

import { CodeEditor } from '../components/CodeEditor';
import { Terminal } from '../components/Terminal';
import { Header } from '../components/Header';
import { FileExplorer } from '../components/FileExplorer';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';

export default function Home() {
  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900 text-white overflow-hidden">
      <Header />
      
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          {/* File Explorer Sidebar */}
          <Panel defaultSize={20} minSize={15} maxSize={40} className="border-r border-gray-700">
            <FileExplorer />
          </Panel>

          <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-500 transition-all duration-200 cursor-col-resize" />

          {/* Main Content Area */}
          <Panel defaultSize={80}>
            <PanelGroup direction="horizontal" className="h-full">
              {/* Editor Section */}
              <Panel defaultSize={60} minSize={30} className="border-r border-gray-700">
                <div className="h-full flex flex-col">
                  <div className="bg-gray-800 px-4 py-3 border-b border-gray-600 flex-shrink-0 flex items-center gap-2">
                    <span className="text-lg">📝</span>
                    <h2 className="text-sm font-semibold text-gray-200">Code Editor</h2>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <CodeEditor />
                  </div>
                </div>
              </Panel>

              <PanelResizeHandle className="w-1.5 bg-gray-700 hover:bg-gray-500 transition-all duration-200 cursor-col-resize" />

              {/* Terminal Section */}
              <Panel defaultSize={40} minSize={25}>
                <div className="h-full flex flex-col">
                  <div className="bg-gray-800 px-4 py-3 border-b border-gray-600 flex-shrink-0 flex items-center gap-2">
                    <span className="text-lg">💻</span>
                    <h2 className="text-sm font-semibold text-gray-200">Terminal</h2>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <Terminal />
                  </div>
                </div>
              </Panel>
            </PanelGroup>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}
