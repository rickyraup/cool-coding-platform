# Code Execution Platform Architecture

## Overview
A full-stack web platform that provides users with an isolated Python development environment featuring a code editor, terminal interface, file management, and code review system.

## System Architecture

```
┌────────────────────────────┐
│        Frontend            │
│    (Next.js 15 + React)    │
│                            │
│  ┌──────────────────────┐  │
│  │    Monaco Editor      │  │ Code editing with syntax highlighting
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │   xterm.js Terminal   │  │ Interactive terminal emulation
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  File Explorer Tree   │  │ Workspace file management
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  Reviewer Management  │  │ Self-service reviewer system
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │ HTTP API / WebSocket
             ▼
┌────────────────────────────┐
│         Backend API        │
│      (FastAPI + Python)    │
│                            │
│  ┌──────────────────────┐  │
│  │   Session Manager     │  │ User session lifecycle
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  WebSocket Handler    │  │ Real-time terminal I/O
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ Container Manager     │  │ Docker container lifecycle
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ Workspace Loader      │  │ File sync between DB and containers
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  User & Auth Service  │  │ Authentication + reviewer system
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │ Database queries
             ▼
┌────────────────────────────┐
│     PostgreSQL Database    │
│                            │
│  - users (with reviewer    │
│    level fields)           │
│  - sessions (UUID-based)   │
│  - workspace_items         │
│  - review_requests         │
└────────────────────────────┘

             │ File persistence
             ▼
┌────────────────────────────┐
│     Docker Containers      │
│   (Per-session isolation)  │
│                            │
│  - Python 3.11 + pandas   │
│  - Isolated file systems  │
│  - Real-time command exec │
│  - Secure sandboxing      │
└────────────────────────────┘
```

## Key Components

### Frontend (Next.js 15)
- **Framework:** Next.js 15 with App Router + React 19
- **Language:** TypeScript with strict mode
- **Styling:** TailwindCSS v4
- **Editor:** Monaco Editor for code editing
- **Terminal:** xterm.js for terminal emulation
- **State Management:** React Context + custom hooks
- **Real-time:** WebSocket connection for terminal I/O

### Backend (FastAPI)
- **Framework:** FastAPI with async/await support
- **Language:** Python 3.9+ with type hints
- **Database:** PostgreSQL with custom connection pooling
- **Authentication:** Simple username/password (extensible)
- **Containerization:** Docker for code execution isolation
- **WebSocket:** Real-time terminal communication
- **Background Tasks:** Container lifecycle management

### Database (PostgreSQL)
- **Users:** Authentication + reviewer system
- **Sessions:** UUID-based session management
- **Workspace Items:** Hierarchical file storage
- **Review Requests:** Code review workflow

### Infrastructure
- **Containers:** Docker for secure Python execution
- **File Storage:** Database-backed with container sync
- **Security:** Sandboxed execution environments
