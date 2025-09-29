# Frontend - Code Execution Platform

Modern Next.js 15 frontend application providing a comprehensive web-based Python development environment.

## 🚀 Features

- **Monaco Code Editor** - VS Code-like editing experience with syntax highlighting
- **Interactive Terminal** - Real-time terminal emulation with xterm.js
- **File Explorer** - Hierarchical workspace management
- **User Authentication** - Registration and login system
- **Code Review System** - Workspace review and approval workflow
- **Responsive Design** - Mobile-friendly interface with dark theme

## 🛠️ Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict mode
- **Styling**: TailwindCSS v4
- **Build Tool**: Turbopack (faster builds)
- **Editor**: Monaco Editor (@monaco-editor/react)
- **Terminal**: xterm.js (@xterm/xterm)
- **State Management**: React Context + custom hooks

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── dashboard/          # User dashboard page
│   ├── reviews/            # Code review pages
│   ├── review/             # Individual review pages
│   │   └── [sessionId]/   # Review workspace routes
│   ├── workspace/          # Code workspace pages
│   │   └── [id]/          # Dynamic workspace routes
│   ├── layout.tsx         # Root layout with fonts
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── Auth.tsx          # Authentication modal
│   ├── CodeEditor.tsx    # Monaco editor wrapper
│   ├── FileExplorer.tsx  # Workspace file tree
│   ├── Header.tsx        # Navigation header
│   ├── ReviewActionModal.tsx # Review action modal
│   ├── ReviewerWorkspace.tsx # Review workspace component
│   ├── ReviewSubmissionModal.tsx # Code review modal
│   ├── Terminal.tsx      # xterm.js terminal
│   ├── WorkspaceShutdownLoader.tsx # Shutdown loader
│   └── WorkspaceStartupLoader.tsx # Startup loader
├── contexts/             # React contexts
│   ├── AppContext.tsx    # Global app state
│   └── AuthContext.tsx   # Authentication state
├── hooks/                # Custom React hooks
│   ├── useWebSocket.ts   # WebSocket communication
│   └── useWorkspaceApi.ts # Workspace API operations
├── services/             # API and service layer
│   ├── api.ts           # Backend API client
│   ├── auth.ts          # Authentication utilities
│   └── workspaceApi.ts  # Workspace file operations
└── utils/                # Utility functions
    └── cache.ts         # API response caching
```

## 🚦 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your backend API URL

# Start development server
npm run dev
```

### Environment Variables
Create `.env.local` with:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws
```

## 📜 Available Scripts

```bash
# Development server with Turbopack
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run ESLint
npm run lint

# Fix ESLint errors
npm run lint:fix

# TypeScript type checking
npm run type-check

# Run all checks
npm run check-all
```

## 🔧 Development

### Code Standards
- **TypeScript**: Strict mode with comprehensive type annotations
- **ESLint**: Enforced code quality and style rules
- **Function Types**: All functions must have explicit return types
- **Component Structure**: Functional components with TypeScript interfaces
- **State Management**: React Context for global state, local state for components

### Key Components

#### CodeEditor
- Monaco Editor integration
- Python syntax highlighting
- Auto-completion and IntelliSense
- File saving with Ctrl+S
- Real-time code validation

#### Terminal
- xterm.js terminal emulation
- WebSocket communication with backend
- Real-time command execution
- Copy/paste support
- Terminal resizing

#### FileExplorer
- Hierarchical file tree display
- File creation and deletion
- Folder navigation
- Context menu operations
- Drag and drop support

#### Authentication
- User registration and login
- JWT token management
- Protected routes
- User profile management

### WebSocket Integration

The frontend uses WebSocket for real-time communication:

```typescript
// WebSocket connection for terminal
const { isConnected, executeCode, manualSave } = useWebSocket();

// Execute code in terminal
executeCode(code, filename);

// Manual file save
manualSave();
```

### API Integration

All backend communication through API service:

```typescript
import { apiService } from '../services/api';

// User management
const user = await apiService.getCurrentUser();
await apiService.toggleReviewerStatus(true, 1);

// Session management
const session = await apiService.createSession({ user_id, name });
const workspace = await apiService.getSessionWithWorkspace(sessionId);

// File operations
await apiService.updateWorkspaceFileContent(sessionId, path, content);
```

## 🎨 Styling

- **TailwindCSS v4**: Utility-first CSS framework
- **Dark Theme**: Professional development environment
- **Responsive Design**: Mobile-first approach
- **Component Styling**: Consistent design system
- **Custom Fonts**: Geist Sans and Geist Mono

### Design System
- **Colors**: Gray-based with blue/purple accents
- **Spacing**: Consistent rem-based spacing
- **Typography**: Clear hierarchy with appropriate font weights
- **Shadows**: Subtle depth for interactive elements

## 🔒 Security

- **Input Validation**: Client-side validation with server-side verification
- **XSS Prevention**: Proper content sanitization
- **CSRF Protection**: CSRF tokens where needed
- **Authentication**: Secure token storage and management

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🧪 Testing

```bash
# Run ESLint checks
npm run lint

# TypeScript compilation check
npm run type-check

# All quality checks
npm run check-all
```

## 📚 Dependencies

### Core Dependencies
- `next`: React framework
- `react`: UI library
- `react-dom`: React DOM renderer
- `@monaco-editor/react`: Code editor
- `@xterm/xterm`: Terminal emulation
- `react-resizable-panels`: Resizable layout panels

### Development Dependencies
- `typescript`: Type checking
- `eslint`: Code linting
- `tailwindcss`: CSS framework
- `@types/*`: TypeScript definitions

## 🚀 Deployment

### Production Build
```bash
npm run build
npm start
```

### Deployment Platforms
- **Vercel** (recommended for Next.js)
- **Netlify**
- **Railway**
- **AWS/GCP/Azure**

### Environment Setup
1. Set `NEXT_PUBLIC_API_URL` to production backend URL
2. Set `NEXT_PUBLIC_WS_URL` to production WebSocket URL
3. Configure any additional environment variables
4. Ensure CORS is configured on backend for frontend domain

## 🐛 Troubleshooting

### Common Issues

1. **Port 3000 in use**: App will automatically use next available port
2. **API connection failed**: Check backend server is running on configured port
3. **WebSocket connection issues**: Verify WebSocket URL and backend WebSocket endpoint
4. **Build errors**: Run `npm run type-check` to identify TypeScript issues

### Debug Mode
Add to `.env.local`:
```env
NODE_ENV=development
NEXT_PUBLIC_DEBUG=true
```

## 🤝 Contributing

1. Follow TypeScript and ESLint conventions
2. Add proper type annotations
3. Test components thoroughly
4. Update documentation for new features
5. Ensure responsive design compatibility