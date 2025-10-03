# Frontend - Code Execution Platform

Modern Next.js 15 frontend application providing a comprehensive web-based Python development environment with real-time code execution, file management, and interactive terminal.

## 🚀 Features

- **Monaco Code Editor** - VS Code-like editing experience with Python syntax highlighting
- **Interactive Terminal** - Real-time terminal emulation with xterm.js and WebSocket communication
- **File Explorer** - Create, edit, delete files and navigate your workspace
- **User Authentication** - Secure registration and login with session management
- **Live Workspace Management** - Create and manage isolated development workspaces
- **Real-time Code Execution** - Execute Python code with instant terminal output
- **Kubernetes-backed Isolation** - Each workspace runs in isolated Kubernetes pods
- **Responsive Design** - Mobile-friendly interface with professional dark theme

## 🛠️ Tech Stack

- **Framework**: Next.js 15.5.2 with App Router
- **Language**: TypeScript 5+ with strict mode enabled
- **Styling**: TailwindCSS v4 with PostCSS
- **Build Tool**: Turbopack (2-3x faster than Webpack)
- **Editor**: Monaco Editor (@monaco-editor/react)
- **Terminal**: xterm.js (@xterm/xterm) with FitAddon and WebLinksAddon
- **State Management**: React Context API + custom hooks
- **Real-time Communication**: WebSocket for terminal I/O
- **Code Quality**: ESLint with Next.js recommended rules + custom rules

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                     # Next.js App Router pages
│   │   ├── dashboard/           # User workspace dashboard
│   │   │   └── page.tsx         # List all workspaces, create new ones
│   │   ├── workspace/
│   │   │   └── [id]/            # Dynamic workspace route
│   │   │       └── page.tsx     # Main workspace IDE (editor + terminal + file explorer)
│   │   ├── layout.tsx           # Root layout with fonts + metadata
│   │   ├── page.tsx             # Landing page with auth
│   │   └── globals.css          # Global styles + Tailwind directives
│   │
│   ├── components/              # React components
│   │   ├── Auth.tsx             # Login/signup modal
│   │   ├── CodeEditor.tsx       # Monaco editor wrapper with save/execute
│   │   ├── FileExplorer.tsx     # File tree with create/delete/navigate
│   │   ├── Header.tsx           # Navigation with user menu + workspace controls
│   │   ├── Terminal.tsx         # xterm.js terminal with WebSocket integration
│   │   ├── WorkspaceShutdownLoader.tsx  # Shutdown animation
│   │   └── WorkspaceStartupLoader.tsx   # Startup animation
│   │
│   ├── contexts/                # React Context providers
│   │   ├── AppContext.tsx       # Global app state (files, code, terminal, sessions)
│   │   └── AuthContext.tsx      # User authentication state + login/register/logout
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── useWebSocket.ts      # WebSocket connection for real-time terminal I/O
│   │
│   ├── services/                # API service layer
│   │   ├── api.ts               # Main API client with all backend endpoints
│   │   └── workspaceApi.ts      # Workspace-specific file operations
│   │
│   ├── types/                   # TypeScript type definitions
│   │   └── css.d.ts             # CSS module types

│
├── public/                      # Static assets
├── eslint.config.js            # ESLint flat config (v9+)
├── next.config.ts              # Next.js configuration with Turbopack
├── postcss.config.mjs          # PostCSS + TailwindCSS v4 plugin
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies and scripts
```

## 🏗️ Architecture & How Everything Connects

### Frontend → Backend Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  Dashboard  │───▶│  Workspace   │───▶│  Components   │  │
│  │    Page     │    │    Page      │    │  (IDE Layout) │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
│         │                   │                    │           │
│         └───────────────────┴────────────────────┘           │
│                             │                                │
│         ┌───────────────────▼─────────────────────┐         │
│         │        AppContext (Global State)        │         │
│         │  - Files, Code, Terminal, Sessions      │         │
│         └───────────────────┬─────────────────────┘         │
│                             │                                │
│         ┌───────────────────▼─────────────────────┐         │
│         │      Custom Hooks (Business Logic)      │         │
│         │  - useWebSocket: Terminal I/O           │         │
│         │       │         │
│         └───────────────────┬─────────────────────┘         │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        REST API          WebSocket        REST API
    (HTTP/HTTPS)        (Terminal I/O)    (Files)
              │               │               │
              ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI + Python)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Auth        │    │  Sessions    │    │  Workspaces   │  │
│  │ /api/auth/* │    │  /api/session│    │  /api/files/* │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
│         │                   │                    │           │
│         └───────────────────┴────────────────────┘           │
│                             │                                │
│         ┌───────────────────▼─────────────────────┐         │
│         │        WebSocket Manager (/ws)          │         │
│         │  - Terminal command execution           │         │
│         │  - File read/write/list operations      │         │
│         └───────────────────┬─────────────────────┘         │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Kubernetes Cluster (kind)   │
              │  - Execution pods (1 per user)│
              │  - Python 3.11 + packages     │
              │  - Isolated file systems      │
              └───────────────────────────────┘
```

### Data Flow Examples

#### 1. User Creates New Workspace
```
Dashboard → apiService.createSession() → Backend creates K8s pod →
Poll workspace status → Workspace ready → Navigate to /workspace/[id]
```

#### 2. User Edits and Saves File
```
CodeEditor onChange → AppContext.updateCode() →
User hits Cmd+S → useWebSocket.manualSave() →
WebSocket 'save_file' message → Backend writes to pod filesystem
```

#### 3. User Executes Python Code
```
Terminal input → useWebSocket.sendTerminalCommand() →
WebSocket 'terminal_input' → Backend executes in K8s pod →
Output via WebSocket → Terminal displays result
```

#### 4. User Opens File
```
FileExplorer click → useWebSocket.performFileOperation('read', path) →
Backend reads from pod → WebSocket sends content →
AppContext.setFileContent() → CodeEditor displays code
```

## 🚦 Quick Start

### Prerequisites
- **Node.js 18+** (LTS recommended)
- **npm 9+** or **yarn 1.22+**
- **Backend server running** (see `/backend/README.md`)

### Installation & Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local with your settings:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Start development server with Turbopack
npm run dev
```

The app will start on `http://localhost:3000` (or next available port).

### Environment Variables

Create `.env.local` in the frontend root:

```env
# Backend API URL (HTTP)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend WebSocket URL (WS)
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional: Debug mode
NEXT_PUBLIC_DEBUG=false
```

**Production:**
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

## 📜 Available Scripts

```bash
# Development server with Turbopack (hot reload, faster builds)
npm run dev

# Production build with optimizations
npm run build

# Start production server (after build)
npm start

# Run ESLint to check for code quality issues
npm run lint

# Auto-fix ESLint issues (use cautiously)
npm run lint -- --fix

# TypeScript type checking (no build)
npm run type-check

# Run all quality checks (lint + type-check)
npm run check-all
```

### Development Workflow

1. **Start backend:** `cd backend && source venv/bin/activate && python -m app.main`
2. **Start frontend:** `cd frontend && npm run dev`
3. **Open browser:** Navigate to `http://localhost:3000`
4. **Create account:** Sign up with email, username, password
5. **Create workspace:** Click "New Workspace" on dashboard
6. **Start coding:** Edit files in Monaco editor, run code in terminal

## 🔧 ESLint Configuration

### Overview

This project uses **ESLint** with strict rules to maintain code quality and consistency. The configuration enforces:

- TypeScript best practices
- React/Next.js specific rules
- Async/await error handling
- Function complexity limits
- Code style consistency

### ESLint Rules Summary

#### ✅ Enabled Rules

| Rule | Purpose | Severity |
|------|---------|----------|
| `@typescript-eslint/no-floating-promises` | Require all promises to be handled | Warning |
| `@typescript-eslint/no-misused-promises` | Prevent promises in wrong contexts | Warning |
| `@typescript-eslint/no-unused-vars` | Remove unused variables | Warning |
| `@typescript-eslint/no-explicit-any` | Avoid `any` types | Warning |
| `react-hooks/exhaustive-deps` | Complete useEffect dependencies | Warning |
| `max-lines-per-function` | Limit function length to 150 lines | Warning |
| `complexity` | Limit cyclomatic complexity to 20 | Warning |

#### Handling Promises

**❌ Wrong:**
```typescript
useEffect(() => {
  fetchData(); // Floating promise - not handled!
}, []);
```

**✅ Correct:**
```typescript
useEffect(() => {
  fetchData().catch(console.error); // Promise handled
}, []);
```

#### React Hooks Dependencies

**❌ Wrong:**
```typescript
useEffect(() => {
  doSomething(value);
}, []); // Missing 'value' dependency
```

**✅ Correct:**
```typescript
useEffect(() => {
  doSomething(value);
}, [value]); // All dependencies included
```

### Running ESLint

```bash
# Check for issues
npm run lint

# Auto-fix safe issues
npm run lint -- --fix

# Check specific file
npm run lint -- src/app/page.tsx

# Check with detailed output
npm run lint -- --format stylish
```

### ESLint in CI/CD

ESLint runs automatically in:
- **Pre-commit hooks** (if configured)
- **GitHub Actions** (`.github/workflows/code_checks.yaml`)
- **Pull request checks**

## 🧩 Key Components Deep Dive

### 1. AppContext (`src/contexts/AppContext.tsx`)

Central state management for the entire application.

**State:**
```typescript
{
  currentSession: Session | null,
  files: FileItem[],
  currentFile: string | null,
  code: string,
  terminalLines: TerminalLine[],
  fileContents: { [path: string]: string },
  fileSavedStates: { [path: string]: boolean },
  hasUnsavedChanges: boolean,
  isAutosaveEnabled: boolean,
  isLoading: boolean
}
```

**Key Functions:**
- `setSession()` - Set current workspace session
- `updateCode()` - Update current file code
- `addTerminalLine()` - Add output to terminal
- `setFiles()` - Update file tree
- `hasFileUnsavedChanges()` - Check if file has unsaved changes

### 2. useWebSocket Hook (`src/hooks/useWebSocket.ts`)

Manages WebSocket connection to backend for real-time communication.

**Features:**
- Auto-reconnection on disconnect
- Message queue for offline messages
- File operations via WebSocket (read, write, list)
- Terminal I/O streaming
- Connection status tracking

**Usage:**
```typescript
const {
  isConnected,
  sendTerminalCommand,
  performFileOperation,
  manualSave
} = useWebSocket();

// Execute command in terminal
sendTerminalCommand('python main.py');

// Read file from workspace
performFileOperation('read', 'main.py');

// Save current file
manualSave(code, filename);
```

### 3. CodeEditor Component (`src/components/CodeEditor.tsx`)

Monaco editor wrapper with keyboard shortcuts and auto-save.

**Features:**
- Python syntax highlighting
- Ctrl+S to save
- Auto-completion
- Line numbers
- Minimap
- Find & replace

**Configuration:**
```typescript
<Editor
  height="100%"
  defaultLanguage="python"
  theme="vs-dark"
  value={code}
  onChange={handleChange}
  options={{
    fontSize: 14,
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    automaticLayout: true
  }}
/>
```

### 4. Terminal Component (`src/components/Terminal.tsx`)

xterm.js terminal with full terminal emulation.

**Features:**
- Command history (up/down arrows)
- Copy/paste (Ctrl+C/V)
- Terminal resizing
- ANSI color codes
- Progress indicators
- WebSocket integration

**Implementation:**
```typescript
const terminal = new XTerm({
  theme: {
    background: '#000000',
    foreground: '#ffffff',
    cursor: '#00ff00'
  },
  fontFamily: '"Courier New", Courier, monospace',
  fontSize: 14,
  cursorBlink: true
});

terminal.loadAddon(new FitAddon());
terminal.loadAddon(new WebLinksAddon());
```

### 5. FileExplorer Component (`src/components/FileExplorer.tsx`)

File tree navigator with CRUD operations.

**Features:**
- Create new files/folders
- Delete files (with confirmation)
- Open files in editor
- Run Python files directly
- File type icons
- Unsaved changes indicator (dot)

**File Operations:**
- **Create:** Input dialog → WebSocket 'save_file' → Refresh list
- **Delete:** Confirmation modal → API call → Refresh list
- **Open:** Click file → WebSocket 'read' → Load in editor
- **Run:** Play button → Send `python3 {file}` to terminal

## 🎨 Styling & Design System

### TailwindCSS v4

Using utility-first CSS with custom configuration.

**Color Palette:**
```
Gray scale:  gray-50 → gray-950 (backgrounds, text)
Primary:     blue-500, blue-600, blue-700
Secondary:   purple-500, purple-600
Success:     green-400, green-500
Warning:     yellow-400, yellow-500
Error:       red-400, red-500, red-600
```

**Component Patterns:**
```typescript
// Button (primary)
className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"

// Input field
className="px-3 py-2 bg-gray-800 border border-gray-700 text-white rounded-lg focus:border-blue-500 focus:outline-none"

// Card container
className="bg-gray-800 rounded-lg p-6 border border-gray-700"
```

### Responsive Design

Mobile-first with breakpoints:
```
sm:  640px  (small tablets)
md:  768px  (tablets)
lg:  1024px (laptops)
xl:  1280px (desktops)
2xl: 1536px (large desktops)
```

## 🔒 Security Considerations

### Authentication
- User data stored in `localStorage` for session persistence
- User ID and profile cached client-side
- Server-side session validation on each request
- Password requirements enforced (8+ chars, uppercase, lowercase, number, special char)

### Input Validation
- Client-side validation for UX
- Server-side validation for security
- XSS prevention via React's built-in escaping
- No `dangerouslySetInnerHTML` usage

### WebSocket Security
- Same-origin policy enforced
- User session validation on WebSocket connection
- Input sanitization for terminal commands
- Isolated execution environments per user

## 🧪 Code Quality & Testing

### TypeScript Strict Mode

All files use strict TypeScript:
```typescript
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### ESLint Stats (Current)

- **Errors:** 0 ✅
- **Warnings:** 0 ✅
- **Files checked:** All `.ts` and `.tsx` files

## 🚀 Deployment

### Production Build

```bash
# Build optimized production bundle
npm run build

# Output directory: .next/
# Static pages pre-rendered at build time
# Dynamic routes handled by Next.js server

# Start production server
npm start
```

### Deployment Platforms

#### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

#### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables (Production)

Set in deployment platform:
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

### CORS Configuration

Backend must allow frontend domain:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 Troubleshooting

### Common Issues

#### Port 3000 Already in Use
```bash
# Next.js will auto-select next available port
# Or specify custom port:
PORT=3001 npm run dev
```

#### API Connection Failed
```bash
# Check backend is running:
curl http://localhost:8000/api/health

# Check .env.local has correct URL:
cat .env.local | grep API_URL
```

#### WebSocket Connection Issues
```bash
# Check WebSocket URL format (ws:// not http://)
# Check backend WebSocket endpoint is active
# Check browser console for WebSocket errors
```

#### TypeScript Errors
```bash
# Clean build cache
rm -rf .next

# Re-install dependencies
rm -rf node_modules package-lock.json
npm install

# Run type check
npm run type-check
```

#### ESLint Errors on Import
```bash
# Clear ESLint cache
rm -rf .eslintcache

# Re-run ESLint
npm run lint
```

## 📦 Dependencies

### Production Dependencies
```json
{
  "next": "15.5.2",
  "react": "^19.0.0",
  "react-dom": "^19.0.0",
  "@monaco-editor/react": "^4.6.0",
  "@xterm/xterm": "^5.5.0",
  "@xterm/addon-fit": "^0.10.0",
  "@xterm/addon-web-links": "^0.11.0",
  "react-resizable-panels": "^2.1.7",
  "sonner": "^1.7.1"
}
```

### Development Dependencies
```json
{
  "typescript": "^5",
  "eslint": "^9",
  "@typescript-eslint/eslint-plugin": "^8",
  "@typescript-eslint/parser": "^8",
  "tailwindcss": "^4",
  "postcss": "^8"
}
```

## 🤝 Contributing

### Code Style
1. Use TypeScript strict mode
2. Follow ESLint rules (run `npm run lint` before commit)
3. Add JSDoc comments for complex functions
4. Use functional components with hooks
5. Keep components under 150 lines (refactor if needed)

### Pull Request Process
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run quality checks: `npm run check-all`
4. Commit with descriptive message
5. Push and create PR on GitHub
6. Wait for CI checks to pass

### Commit Message Format
```
type(scope): Short description

Longer explanation if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 📝 Changelog

### Version 2.0 (Current)
- ✅ Removed code review system (simplified architecture)
- ✅ Improved WebSocket reliability with reconnection
- ✅ Enhanced file explorer with better UX
- ✅ Fixed all ESLint errors
- ✅ Updated to TailwindCSS v4
- ✅ Upgraded to Next.js 15.5.2

### Version 1.0
- Initial release with review system
- Basic workspace functionality
- Monaco editor + xterm.js integration

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [Monaco Editor API](https://microsoft.github.io/monaco-editor/)
- [xterm.js Documentation](https://xtermjs.org/)
- [Backend README](../backend/README.md)

## 📧 Support

For issues or questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Search [GitHub Issues](https://github.com/yourusername/repo/issues)
3. Create new issue with detailed description

---

**Note:** The code review/submission system has been removed in version 2.0. If you need this feature, check out version 1.0 in git history.

Built with ❤️ using Next.js, TypeScript, and TailwindCSS
