# FastAPI Backend - Code Execution Platform

This is the FastAPI backend for the Code Execution Platform that provides secure code execution in Kubernetes pods with integrated terminal functionality and persistent workspace management.

## Architecture Overview

The backend uses:
- **FastAPI** for REST API and WebSocket endpoints
- **PostgreSQL (Supabase)** for persistent data storage
- **Kubernetes** for isolated code execution environments
- **WebSockets** for real-time terminal communication
- **UUID-based session management** for workspace isolation

## Recent Updates

- **API Documentation**: Added comprehensive `API.md` with all endpoints, schemas, and examples
- **Models Refactored**: Split monolithic `postgres_models.py` into separate domain files (`users.py`, `sessions.py`, `workspace_items.py`)
- **Schemas Organized**: Created dedicated `workspace.py` schema file for workspace-related Pydantic models
- **Code Cleanup**: Removed review system, guest users, and all debug statements across the codebase
- **Service Refactoring**: Cleaned up unused methods, fixed type issues in kubernetes and container services
- **Type Safety**: Full MyPy strict mode compliance with 0 errors across all source files
- **Linting**: Complete Ruff compliance with all checks passing

## Quick Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Access to a Kubernetes cluster (for code execution)
- PostgreSQL database (Supabase recommended)

### Setup Instructions

#### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
cd backend
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
cd backend
setup.bat
```

#### Option 2: Manual Setup

1. **Create Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate Virtual Environment:**

   **Linux/macOS:**
   ```bash
   source venv/bin/activate
   ```

   **Windows:**
   ```cmd
   venv\Scripts\activate.bat
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Server

1. **Activate virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate.bat  # Windows
   ```

2. **Start the FastAPI server:**
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The server will start on `http://localhost:8000` (default port)

## API Documentation

**📖 Complete API Reference**: See [API.md](./API.md) for detailed endpoint documentation, request/response schemas, and examples.

Once the server is running, you can access:
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health
- **Detailed Health Check**: http://localhost:8000/api/health/detailed

## Project Structure

```
backend/
├── app/
│   ├── api/                    # REST API endpoints
│   │   ├── health.py           # Health check endpoints
│   │   ├── sessions.py         # Session management (formerly postgres_sessions.py)
│   │   ├── users.py            # User management
│   │   └── workspace_files.py  # Workspace file operations
│   ├── core/                   # Core utilities
│   │   └── postgres.py         # PostgreSQL connection management
│   ├── models/                 # Database models (refactored from postgres_models.py)
│   │   ├── sessions.py         # CodeSession model
│   │   ├── users.py            # User model
│   │   └── workspace_items.py  # WorkspaceItem model (file/folder hierarchy)
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── base.py             # Base response schemas
│   │   ├── sessions.py         # Session schemas
│   │   ├── users.py            # User schemas
│   │   └── workspace.py        # Workspace file schemas
│   ├── services/               # Business logic services
│   │   ├── container_manager.py    # Kubernetes pod session management
│   │   ├── kubernetes_client.py    # Kubernetes API client
│   │   ├── workspace_loader.py     # Workspace file loading
│   │   ├── background_tasks.py     # Background task management
│   │   └── file_manager.py         # File operations
│   ├── websockets/             # WebSocket handling
│   │   ├── manager.py          # WebSocket connection management
│   │   └── handlers.py         # WebSocket message handlers
│   └── main.py                 # FastAPI application entry point
├── tests/                      # Test suite
│   ├── api/                    # API endpoint tests
│   │   ├── test_health.py      # Health endpoint tests
│   │   ├── test_sessions.py    # Session API tests
│   │   └── test_workspace_files.py  # Workspace file API tests
│   ├── test_kubernetes_client.py    # Kubernetes client tests
│   └── conftest.py             # Pytest configuration
├── k8s/                        # Kubernetes manifests
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Python project configuration
├── pytest.ini                  # Pytest configuration
├── mypy.ini                    # MyPy type checker configuration
├── ruff.toml                   # Ruff linter configuration
├── setup.sh                    # Setup script (Linux/macOS)
└── .env                        # Environment variables (not in git)
```

## Features

### REST API Endpoints

#### Health Check
- `GET /api/health/` - Basic health check
- `GET /api/health/detailed` - Detailed health check with system metrics

#### User Management
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - User login

#### Session Management
- `GET /api/sessions/?user_id={user_id}` - List sessions for a user
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/{session_uuid}?user_id={user_id}` - Get session by UUID

#### Workspace File Operations
- `GET /api/workspace/{session_uuid}/files` - List all files in workspace
- `GET /api/workspace/{session_uuid}/file/{filename}` - Get file content
- `POST /api/workspace/{session_uuid}/file/{filename}` - Create/update file
- `DELETE /api/workspace/{session_uuid}/file/{filename}` - Delete file
- `GET /api/workspace/{session_uuid}/status` - Get workspace initialization status
- `POST /api/workspace/{session_uuid}/ensure-default` - Create default files if workspace is empty

#### Workspace Management
- `POST /workspace/{workspace_id}/shutdown` - Gracefully shutdown workspace and cleanup container

### WebSocket Endpoint
- `WS /ws?user_id={user_id}` - Real-time terminal communication
  - Supports terminal input/output
  - Command execution in isolated Kubernetes pods
  - Session persistence across reconnections

### Security Features
- **Isolated Execution**: Each workspace runs in a separate Kubernetes pod
- **Resource Limits**: CPU and memory limits per pod
- **Session Isolation**: UUID-based session IDs prevent session reuse
- **User Authorization**: Access control on session and workspace operations
- **File Persistence**: Files stored in PostgreSQL and synced to pods
- **Automatic Cleanup**: Pods cleaned up when WebSocket disconnects

### Code Execution Environment
- **Python 3.11** runtime
- **Pre-installed packages**: pandas, scipy, numpy, and more
- **Persistent storage**: Files stored in database and mounted to pods
- **Terminal commands**: Full bash terminal access in pods

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Server Configuration
PORT=8000
ENVIRONMENT=production
ENABLE_RELOAD=false  # Set to 'true' for development hot-reload

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Kubernetes Configuration
KUBERNETES_NAMESPACE=default
KUBERNETES_IN_CLUSTER=false  # Set to 'true' when running inside K8s

# Session Configuration
SESSION_TIMEOUT=3600
MAX_FILE_SIZE=1048576
```

## Development

### Code Quality Tools

The project uses several tools to maintain code quality:

```bash
# Type checking with MyPy (strict mode)
venv/bin/mypy app --strict --show-error-codes

# Linting with Ruff
venv/bin/ruff check app/

# Code formatting with Ruff
venv/bin/ruff format app/

# Auto-fix linting issues
venv/bin/ruff check app/ --fix
```

### Running Tests

```bash
# Run all tests
venv/bin/python -m pytest tests/ -v

# Run specific test file
venv/bin/python -m pytest tests/api/test_sessions.py -v

# Run with coverage
venv/bin/python -m pytest tests/ --cov=app --cov-report=html
```

**Note**: Database integration tests are not fully implemented yet. Many tests currently fail due to database mocking issues. This is a known limitation being worked on.

### Adding New Dependencies
```bash
# Activate venv first
source venv/bin/activate

# Install new package
pip install new-package

# Update requirements.txt
pip freeze > requirements.txt
```

### Database Schema

The PostgreSQL database schema includes:

**Tables:**
- `users` - User accounts
- `code_sessions` - Coding sessions (workspace metadata)
- `workspace_items` - File/folder hierarchy for each session

The schema is created automatically when the server starts via the `init_db()` function.

## Deployment

### Kubernetes Deployment

The backend can be deployed to Kubernetes using the manifests in `k8s/`:

```bash
# Deploy backend
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

# Deploy database (if not using external Supabase)
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-pvc.yaml
```

### Docker Build

```bash
# Build backend image
docker build -t backend:latest -f Dockerfile .

# Or use the build script
./build-and-push.sh
```

## Troubleshooting

### Common Issues

1. **Python not found**: Make sure Python 3.9+ is installed and in your PATH
2. **Permission denied**: On Linux/macOS, make sure setup.sh is executable: `chmod +x setup.sh`
3. **Module not found**: Make sure virtual environment is activated and dependencies are installed
4. **Port already in use**: Change the PORT in `.env` file or kill the process using the port
5. **Database connection failed**:
   - Check DATABASE_URL in `.env`
   - Verify database password (was changed due to git leak)
   - Ensure PostgreSQL is running and accessible
6. **Kubernetes connection failed**:
   - Verify `~/.kube/config` exists and is valid
   - Check KUBERNETES_NAMESPACE matches your cluster
   - Ensure you have proper RBAC permissions

### Logs

The server logs all requests, errors, and important events to the console. Check the terminal output for debugging information.

### Debug Mode

To run with hot-reload and debug logging:

```bash
# Set in .env
ENABLE_RELOAD=true

# Or run directly
uvicorn app.main:app --reload --log-level debug
```

## WebSocket Testing

Test the WebSocket connection using:
- The frontend application (recommended)
- `websocat` CLI tool: `websocat ws://localhost:8000/ws`
- Browser DevTools or Postman

Example WebSocket message:
```json
{
  "type": "terminal_input",
  "sessionId": "workspace-uuid-here",
  "input": "ls\n"
}
```

## Contributing

When contributing:
1. Run type checking: `mypy app --strict`
2. Run linter: `ruff check app/`
3. Format code: `ruff format app/`
4. Run tests: `pytest tests/ -v`
5. Update this README and `API.md` if you change API endpoints or add features

## Known Issues & TODOs

- [ ] Implement JWT-based authentication (currently using user_id query parameters)
- [ ] Add WebSocket authentication
- [ ] Complete database integration tests (currently failing due to mocking issues)
- [ ] Add more comprehensive test coverage for WebSocket handlers
- [ ] Implement rate limiting for API endpoints
- [ ] Add metrics and monitoring endpoints
- [ ] Add file upload/download endpoints
- [ ] Implement session sharing between users

## License

[Add your license here]
