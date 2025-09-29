# Code Execution Platform

A modern web-based development environment that provides users with an isolated Python development environment featuring a code editor, terminal interface, file management, and collaborative code review system.

![Platform Demo](https://img.shields.io/badge/Status-Production%20Ready-green)
![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%2B%20FastAPI-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen)

## 🚀 Features

### Core Development Environment
- **🖥️ Monaco Code Editor**: Full-featured editor with Python syntax highlighting, IntelliSense, and autocomplete
- **📟 Interactive Terminal**: Real-time terminal emulation with xterm.js supporting all standard commands
- **📁 File Management**: Create, edit, and organize files in a hierarchical workspace structure
- **💾 Session Persistence**: Multiple isolated sessions per user with automatic workspace saving
- **🔒 Secure Execution**: Docker-containerized Python environment with resource limits

### Advanced Features
- **👥 User Management**: Registration, authentication, and profile management
- **📝 Code Review System**: Submit code for review with priority levels and reviewer assignment
- **🏆 Reviewer Levels**: Self-service promotion to Junior or Senior reviewer status
- **🔄 Real-time Sync**: WebSocket-based live updates between editor and terminal
- **🐍 Python Environment**: Pre-installed with pandas, scipy, numpy, and pip package management

### Security & Performance
- **🛡️ Sandboxed Execution**: Each session runs in an isolated Docker container
- **⚡ Resource Management**: Memory, CPU, and time limits to prevent abuse
- **🔐 Input Validation**: Comprehensive validation and sanitization
- **📊 Monitoring**: Real-time resource usage and session management

## 🏗️ Architecture

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict mode
- **Styling**: TailwindCSS v4
- **Editor**: Monaco Editor
- **Terminal**: xterm.js with full TTY support
- **State**: React Context + custom hooks

### Backend (FastAPI)
- **Framework**: FastAPI with async/await
- **Language**: Python 3.9+ with type hints
- **Database**: PostgreSQL with custom ORM
- **Containers**: Docker for secure code execution
- **WebSocket**: Real-time terminal communication
- **Background Tasks**: Container lifecycle management

### Database Schema
- **Users**: Authentication + reviewer system
- **Sessions**: UUID-based workspace management
- **Workspace Items**: Hierarchical file storage
- **Review Requests**: Code review workflow

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 15 + React 19 | Modern web framework with SSR |
| **Backend** | FastAPI + Python 3.11 | High-performance async API |
| **Database** | PostgreSQL | Reliable relational database |
| **Editor** | Monaco Editor | VS Code-like editing experience |
| **Terminal** | xterm.js | Full terminal emulation |
| **Styling** | TailwindCSS v4 | Utility-first CSS framework |
| **Containers** | Docker | Secure code execution isolation |
| **Real-time** | WebSocket | Live terminal communication |

## 📁 Project Structure

```
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # App Router pages and layouts
│   │   ├── components/         # React components
│   │   ├── contexts/           # React contexts (Auth, App state)
│   │   ├── hooks/              # Custom React hooks
│   │   └── services/           # API service layer
│   ├── public/                 # Static assets
│   └── package.json            # Frontend dependencies
├── backend/                     # FastAPI backend service
│   ├── app/
│   │   ├── api/                # REST API endpoints
│   │   ├── core/               # Core utilities (database, settings)
│   │   ├── models/             # Database models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic services
│   │   ├── websockets/         # WebSocket handlers
│   │   └── main.py             # FastAPI application entry point
│   ├── tests/                  # Comprehensive test suite
│   ├── migrations/             # Database migrations
│   └── requirements.txt        # Python dependencies
├── docs/                        # Project documentation
│   ├── SETUP.md                # Complete setup guide
│   ├── FEATURES.md             # Detailed feature documentation
│   ├── api/                    # API documentation
│   │   ├── README.md           # API overview
│   │   ├── reviews.md          # Review system API
│   │   ├── users.md            # User management API
│   │   ├── workspace.md        # Workspace operations API
│   │   └── websocket.md        # WebSocket API
│   ├── architecture/           # Architecture documentation
│   │   └── ARCHITECTURE.md     # System design and components
│   ├── database/               # Database documentation
│   │   └── DATABASE.md         # Schema design and models
│   └── deployment/             # Deployment guides
│       └── README.md           # Production deployment guide
└── README.md                   # This file
```

## 🚦 Quick Start

### Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.9+ (for backend)
- **PostgreSQL** 14+ (database)
- **Docker** 20+ (for code execution)

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Start the server
python -m app.main
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with API URL

# Start development server
npm run dev
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## 📚 Documentation

### 🚀 Getting Started
- **[Setup Guide](docs/SETUP.md)** - Complete installation and configuration
- **[Features](docs/FEATURES.md)** - Detailed feature documentation
- **[Deployment Guide](docs/deployment/README.md)** - Production deployment strategies

### 🏗️ Technical Reference
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design and components
- **[Database](docs/database/DATABASE.md)** - Schema design and data models
- **[API Documentation](docs/api/README.md)** - Complete API reference

### 🔌 API Endpoints
- **[Reviews API](docs/api/reviews.md)** - Code review system endpoints
- **[Users API](docs/api/users.md)** - User management and authentication
- **[Workspace API](docs/api/workspace.md)** - File and session operations
- **[WebSocket API](docs/api/websocket.md)** - Real-time terminal communication

## 🔧 Development

### Running Tests
```bash
# Backend tests
cd backend
venv/bin/python -m pytest tests/ -v

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

### Database Setup
```bash
# Create PostgreSQL database
createdb coolcoding
createuser -s coolcoding_user

# Run migrations (automatic on startup)
python -m app.main
```

## 🔒 Security Features

- **Container Isolation**: Each session runs in a separate Docker container
- **Resource Limits**: Memory, CPU, and execution time constraints
- **Input Validation**: Comprehensive sanitization of all inputs
- **Path Protection**: Prevention of directory traversal attacks
- **Session Isolation**: User data completely separated
- **Rate Limiting**: Protection against abuse and DoS attacks

## 🌟 Key Workflows

### Basic Development Session
1. User registers/logs in
2. Creates a new coding session
3. Writes Python code in Monaco editor
4. Executes code in interactive terminal
5. Files are automatically saved to database
6. Session state persists between visits

### Code Review Process
1. Developer completes code in session
2. Submits code for review with description and priority
3. Available reviewers can claim and review submissions
4. Reviewers provide feedback and approve/reject code
5. Developers receive notifications and can iterate

### Reviewer System
1. Any user can self-promote to reviewer status
2. Choose between Junior Reviewer (Level 1) or Senior Reviewer (Level 2)
3. Reviewers are listed and available for selection
4. Senior reviewers can mentor and guide development standards

## 🚀 Deployment

### Production Deployment
- **Frontend**: Deploy to Vercel, Netlify, or similar
- **Backend**: Deploy to Railway, Render, or cloud provider
- **Database**: Use managed PostgreSQL (Supabase, AWS RDS)
- **Containers**: Ensure Docker is available on backend host

### Environment Configuration
- Configure production database URLs
- Set up CORS for frontend domain
- Enable HTTPS for secure WebSocket connections
- Configure container resource limits

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Built with ❤️ using Next.js, FastAPI, and modern web technologies**