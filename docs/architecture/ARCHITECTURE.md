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
│  │  Code Review System   │  │ Review workflow + workspace review
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
│  ┌──────────────────────┐  │
│  │   Review Service      │  │ Code review request management
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │    File Sync Service  │  │ Sync files between API and containers
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

## Current System Features

### Code Review System
- **Review Workflow:** Submit workspaces for review with priority levels
- **Status Tracking:** pending → in_review → approved/rejected
- **Reviewer Management:** Self-service reviewer promotion system
- **Review Interface:** Dedicated review workspace with read-only code view

### Authentication & Authorization
- **User Management:** Username/password authentication
- **Session Management:** Server-side session tracking
- **Reviewer System:** Multi-level reviewer permissions (Level 1-4)
- **Access Control:** Role-based access to review functions

### Workspace Management
- **Session Isolation:** Each workspace gets unique container environment
- **File Persistence:** Files synchronized between database and containers
- **Real-time Collaboration:** WebSocket-based terminal sharing
- **Container Lifecycle:** Automatic cleanup when sessions end

### API Architecture
- **RESTful Design:** Standard HTTP methods for resource operations
- **WebSocket Integration:** Real-time terminal communication
- **Error Handling:** Consistent error response format
- **Type Safety:** Full TypeScript coverage on frontend

## Security Considerations

### Container Security
- **Process Isolation:** Each user session runs in separate container
- **Resource Limits:** Memory and CPU constraints per container
- **Network Isolation:** Limited network access from containers
- **File System Isolation:** No access to host file system

### Application Security
- **Input Validation:** All user inputs validated on backend
- **SQL Injection Prevention:** Parameterized queries throughout
- **XSS Protection:** Content sanitization on frontend
- **CORS Configuration:** Restricted to allowed origins

### Data Protection
- **Session Security:** Secure session management
- **Code Privacy:** User code only accessible to owner and assigned reviewers
- **Audit Logging:** Container and review actions logged
- **Data Encryption:** Sensitive data encrypted at rest

## Performance Optimizations

### Container Management
- **Lazy Loading:** Containers created only when needed
- **Session Reuse:** Multiple WebSocket connections can share containers
- **Background Cleanup:** Automated container lifecycle management
- **Resource Monitoring:** Container resource usage tracking

### Frontend Performance
- **Code Splitting:** Route-based code splitting with Next.js
- **Caching:** API response caching for static data
- **Optimistic Updates:** Immediate UI feedback for user actions
- **WebSocket Efficiency:** Minimal message overhead

### Database Performance
- **Connection Pooling:** Efficient database connection management
- **Query Optimization:** Indexed queries for common operations
- **Data Modeling:** Normalized schema with appropriate relationships
