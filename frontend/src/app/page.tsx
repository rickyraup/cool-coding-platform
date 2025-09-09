'use client';

import { CodeEditor } from '../components/CodeEditor';
import { Terminal } from '../components/Terminal';
import { Header } from '../components/Header';
import { FileExplorer } from '../components/FileExplorer';

export default function Home() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <Header />
      
      <div className="flex-1 flex">
        {/* File Explorer Sidebar */}
        <div className="w-64 border-r border-gray-700">
          <FileExplorer />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {/* Editor Section */}
          <div className="flex-1 flex flex-col border-r border-gray-700">
            <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
              <h2 className="text-sm font-medium text-gray-300">Code Editor</h2>
            </div>
            <div className="flex-1">
              <CodeEditor />
            </div>
          </div>

          {/* Terminal Section */}
          <div className="w-1/2 flex flex-col">
            <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
              <h2 className="text-sm font-medium text-gray-300">Terminal</h2>
            </div>
            <div className="flex-1">
              <Terminal />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
